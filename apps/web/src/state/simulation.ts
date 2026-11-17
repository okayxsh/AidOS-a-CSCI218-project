import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router';
import { ApiError, simApi } from '../api/client';
import type { ControlAction, ReplayVerification, SimEvent, SimSession } from '../api/types';

export type FeedbackSource = 'session' | 'control' | 'event';

export interface SimFeedback {
  source: FeedbackSource;
  tone: 'error' | 'ok';
  message: string;
}

/**
 * One simulation session for the active scenario. The engine owns every value; this hook
 * only keeps the latest session it returned, sends that session's version with each change,
 * and turns engine errors into messages. The session id is mirrored in `?session=` so a
 * refresh reopens it; a session that belongs to another scenario is never shown.
 */
export function useSimulation(scenarioId: string) {
  const [params, setParams] = useSearchParams();
  const urlSession = params.get('session');
  const [session, setSession] = useState<SimSession | null>(null);
  const [loading, setLoading] = useState(Boolean(urlSession));
  const [busy, setBusy] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<SimFeedback | null>(null);
  const [expired, setExpired] = useState<string | null>(null);
  const latest = useRef<SimSession | null>(null);

  const setUrlSession = useCallback(
    (id: string | null) =>
      setParams(
        (prev) => {
          const copy = new URLSearchParams(prev);
          if (id) copy.set('session', id);
          else copy.delete('session');
          return copy;
        },
        { replace: true },
      ),
    [setParams],
  );

  const show = useCallback((next: SimSession | null) => {
    latest.current = next;
    setSession(next);
  }, []);

  // Reopen the session named in the URL, but only if it belongs to this scenario.
  useEffect(() => {
    if (!urlSession || latest.current) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    simApi.get(urlSession).then(
      (found) => {
        if (cancelled) return;
        if (found.scenario_id === scenarioId) show(found);
        else setUrlSession(null);
        setLoading(false);
      },
      (error: unknown) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.kind === 'http' && error.status === 404)
          setExpired(urlSession);
        else
          setFeedback({
            source: 'session',
            tone: 'error',
            message: error instanceof Error ? error.message : String(error),
          });
        setUrlSession(null);
        setLoading(false);
      },
    );
    return () => {
      cancelled = true;
    };
    // Only on mount: later URL updates come from this hook itself.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fail = useCallback(
    async (error: unknown, source: FeedbackSource) => {
      const current = latest.current;
      if (error instanceof ApiError && error.code === 'session_not_found') {
        setExpired(current?.session_id ?? '');
        show(null);
        setUrlSession(null);
        setFeedback(null);
        return;
      }
      if (
        error instanceof ApiError &&
        (error.code === 'version_conflict' || error.code === 'engine_invariant') &&
        current
      ) {
        try {
          const fresh = await simApi.get(current.session_id);
          show(fresh);
          setFeedback({
            source,
            tone: 'error',
            message: `${error.message} Showing the latest state (version ${fresh.version}).`,
          });
          return;
        } catch {
          // Fall through to the original message.
        }
      }
      setFeedback({
        source,
        tone: 'error',
        message: error instanceof Error ? error.message : String(error),
      });
    },
    [setUrlSession, show],
  );

  /** Run one engine call; show its result, or its error, and never a guess. */
  const perform = useCallback(
    async (
      label: string,
      source: FeedbackSource,
      call: () => Promise<SimSession>,
      describe?: (next: SimSession) => string | Omit<SimFeedback, 'source'> | null,
    ) => {
      setBusy(label);
      setFeedback(null);
      try {
        const next = await call();
        show(next);
        setExpired(null);
        setUrlSession(next.session_id);
        const described = describe?.(next);
        if (typeof described === 'string') setFeedback({ source, tone: 'ok', message: described });
        else if (described) setFeedback({ source, ...described });
        return next;
      } catch (error) {
        await fail(error, source);
        return null;
      } finally {
        setBusy(null);
      }
    },
    [fail, setUrlSession, show],
  );

  const create = (policy: 'aidos' | 'aidos_balanced' = 'aidos') =>
    perform('Creating session', 'session', () => simApi.create(scenarioId, policy));

  const control = (action: ControlAction) => {
    const s = latest.current;
    if (!s) return Promise.resolve(null);
    return perform(`${action}`, 'control', () => simApi.control(s.session_id, action, s.version));
  };

  const apply = (event: SimEvent) => {
    const s = latest.current;
    if (!s) return Promise.resolve(null);
    return perform('Applying event', 'event', () => simApi.apply(s.session_id, s.version, event));
  };

  /** Reset and re-apply this session's own events, then compare the engine's outcome hashes. */
  const replay = () => {
    const s = latest.current;
    if (!s) return Promise.resolve(null);
    const before = s.history.map((h) => h.outcome_hash);
    return perform(
      'Replaying events',
      'control',
      async () => {
        const recorded = await simApi.exportSession(s.session_id);
        return simApi.replay(
          s.session_id,
          s.version,
          recorded.events.map((e) => e.event),
        );
      },
      (next) => {
        const after = next.history.map((h) => h.outcome_hash);
        const mismatch = before.findIndex((hash, i) => after[i] !== hash);
        const events = before.length - 1;
        if (mismatch === -1 && after.length === before.length)
          return `Replayed ${events} event${events === 1 ? '' : 's'} from the initial snapshot: all ${before.length} steps reproduced the same outcome hash as the original run.`;
        return `Replay finished, but step ${mismatch === -1 ? before.length : mismatch} differs from the original run.`;
      },
    );
  };

  /** Rebuild a session from an exported script; the engine verifies it against its hashes. */
  const importScript = (document: unknown) => {
    let verification: ReplayVerification | null = null;
    return perform(
      'Loading script',
      'session',
      async () => {
        const result = await simApi.importSession(document);
        verification = result.verification;
        return result.session;
      },
      (next) => {
        const steps = next.history.length;
        const v = verification as ReplayVerification | null;
        if (!v || !v.checked)
          return `Loaded ${steps - 1} events. The script recorded no outcomes to verify against.`;
        return v.matches
          ? `Loaded ${steps - 1} events. All ${steps} recorded outcome hashes match this engine.`
          : {
              tone: 'error',
              message: `Loaded the script, but step ${v.first_mismatch_seq} no longer matches its recorded outcome (recorded with engine ${v.engine_version_recorded ?? 'unknown'}).`,
            };
      },
    );
  };

  const download = async () => {
    const s = latest.current;
    if (!s) return;
    try {
      const document = await simApi.exportSession(s.session_id);
      const blob = new Blob([JSON.stringify(document, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = Object.assign(window.document.createElement('a'), {
        href: url,
        download: `aidos-simulation-${s.scenario_id}-${s.session_id}.json`,
      });
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      await fail(error, 'control');
    }
  };

  return {
    session,
    loading,
    busy,
    feedback,
    expired,
    create,
    control,
    apply,
    replay,
    importScript,
    download,
    dismiss: () => setFeedback(null),
  };
}

export type Simulation = ReturnType<typeof useSimulation>;
