import {
  CircleCheck,
  Download,
  Pause,
  Play,
  PlayCircle,
  Repeat,
  RotateCcw,
  Square,
} from 'lucide-react';
import { useState } from 'react';
import demoScript from '../../../../data/simulations/triage-demo-escalation.json';
import type { ControlAction, ScenarioDetail, SimSession } from '../api/types';
import { EventComposer } from '../components/sim/EventComposer';
import {
  SimAllocation,
  SimExplanation,
  SimLedger,
  SimSummary,
  SimTimeline,
  StepComparison,
} from '../components/sim/SimPanels';
import { ScenarioGate, ScenarioHeader } from '../components/ScenarioGate';
import { Panel } from '../components/ui/Panel';
import { EmptyState } from '../components/ui/States';
import { StatusBadge } from '../components/ui/StatusBadge';
import { formatInt, shortHash } from '../lib/format';
import { POLICY_NAME, STATE_INFO } from '../lib/simulation';
import { useDashboard } from '../state/dashboard';
import { useSimulation, type Simulation } from '../state/simulation';

/** The demo script's scenario: it can only be loaded while that scenario is active. */
const DEMO_SCENARIO = (demoScript as { scenario_id: string }).scenario_id;

const CONTROLS: { action: ControlAction; label: string; Icon: typeof Play }[] = [
  { action: 'start', label: 'Start', Icon: Play },
  { action: 'pause', label: 'Pause', Icon: Pause },
  { action: 'resume', label: 'Resume', Icon: PlayCircle },
  { action: 'complete', label: 'Complete', Icon: Square },
  { action: 'reset', label: 'Reset', Icon: RotateCcw },
];

function Feedback({ sim, sources }: { sim: Simulation; sources: string[] }) {
  const f = sim.feedback;
  if (!f || !sources.includes(f.source)) return null;
  return (
    <p
      className={`sim-feedback sim-feedback--${f.tone}`}
      role={f.tone === 'error' ? 'alert' : 'status'}
    >
      {f.tone === 'ok' && <CircleCheck size={16} aria-hidden="true" />}
      {f.message}
    </p>
  );
}

function ControlBar({ session, sim }: { session: SimSession; sim: Simulation }) {
  const busy = sim.busy !== null;
  const info = STATE_INFO[session.state];
  return (
    <div className="sim-bar">
      <div className="sim-bar__state">
        <StatusBadge tone={info.tone} dot title={info.meaning}>
          {session.state}
        </StatusBadge>
        <span className="sim-bar__meta">
          {session.current.seq} event{session.current.seq === 1 ? '' : 's'} · clock step{' '}
          {session.current.sim_step} · version {session.version} ·{' '}
          <span className="mono">{session.session_id}</span>
        </span>
      </div>
      <div className="sim-bar__actions" role="group" aria-label="Session controls">
        {CONTROLS.map(({ action, label, Icon }) => (
          <button
            key={action}
            type="button"
            className="btn btn--quiet"
            disabled={busy || !session.allowed_actions.includes(action)}
            onClick={() => void sim.control(action)}
          >
            <Icon size={15} aria-hidden="true" />
            {label}
          </button>
        ))}
        <button
          type="button"
          className="btn btn--quiet"
          disabled={busy || session.event_count === 0}
          onClick={() => void sim.replay()}
          title="Reset to the initial snapshot and re-apply this session's events"
        >
          <Repeat size={15} aria-hidden="true" />
          Replay
        </button>
        <button
          type="button"
          className="btn btn--quiet"
          disabled={busy}
          onClick={() => void sim.download()}
        >
          <Download size={15} aria-hidden="true" />
          Export JSON
        </button>
      </div>
      {sim.busy && (
        <p className="sim-bar__busy" role="status">
          {sim.busy}…
        </p>
      )}
    </div>
  );
}

function StartPanel({ detail, sim }: { detail: ScenarioDetail; sim: Simulation }) {
  const [policy, setPolicy] = useState<'aidos' | 'aidos_balanced'>('aidos');
  const busy = sim.busy !== null;
  const demoAvailable = detail.scenario.scenario_id === DEMO_SCENARIO;
  return (
    <EmptyState
      title={
        sim.expired !== null
          ? 'That simulation session no longer exists'
          : 'No simulation session for this scenario'
      }
      action={
        <div className="sim-start">
          <label className="sim-start__policy">
            Recommendation
            <select
              value={policy}
              onChange={(e) => setPolicy(e.target.value as 'aidos' | 'aidos_balanced')}
            >
              <option value="aidos">AidOS (urgency first)</option>
              <option value="aidos_balanced">AidOS balanced (coverage floor)</option>
            </select>
          </label>
          <button
            type="button"
            className="btn btn--accent"
            disabled={busy}
            onClick={() => void sim.create(policy)}
          >
            <Play size={15} aria-hidden="true" />
            {sim.expired !== null ? 'Start a new session' : 'Load into simulator'}
          </button>
          {demoAvailable && (
            <button
              type="button"
              className="btn btn--quiet"
              disabled={busy}
              onClick={() => void sim.importScript(demoScript)}
            >
              <Repeat size={15} aria-hidden="true" />
              Load demo script
            </button>
          )}
        </div>
      }
    >
      {sim.expired !== null ? (
        <>
          Sessions live in the engine&apos;s memory: they expire after two idle hours and vanish
          when the engine restarts. Start a new one from this scenario; an exported JSON file can be
          replayed exactly.
        </>
      ) : (
        <>
          The simulator applies hypothetical events (a new zone, an escalation, a shipment, a loss)
          to this synthetic scenario. After each one the engine rescores urgency, re-runs FCFS,
          urgency greedy and both AidOS policies, checks every plan and explains what changed. It
          does not predict real outcomes.
          {demoAvailable &&
            ' The demo script replays three events: Zone B escalates, Zone D reports, and 30 medical kits are lost.'}
        </>
      )}
    </EmptyState>
  );
}

function Workspace({ detail }: { detail: ScenarioDetail }) {
  const sim = useSimulation(detail.scenario.scenario_id);
  const session = sim.session;

  const blocked = !session
    ? 'No session.'
    : session.allowed_actions.includes('apply_event')
      ? null
      : session.state === 'READY'
        ? 'Start the session to apply events.'
        : session.state === 'PAUSED'
          ? 'Paused: resume to apply events.'
          : `The session is ${session.state}; reset it to apply events.`;

  return (
    <div className="page">
      <ScenarioHeader detail={detail} title="Crisis simulation" showFileStep={false} />
      <p className="sim-disclaimer">
        Hypothetical events on a synthetic scenario. Every number below comes from the engine. The
        simulator shows how the allocation responds to a change; it does not forecast real crises.
      </p>

      {sim.loading ? (
        <p className="policy-row__running" role="status">
          Reopening the session…
        </p>
      ) : !session ? (
        <>
          <Feedback sim={sim} sources={['session', 'control', 'event']} />
          <StartPanel detail={detail} sim={sim} />
        </>
      ) : (
        <>
          <ControlBar session={session} sim={sim} />
          <Feedback sim={sim} sources={['session', 'control']} />
          {session.error && (
            <p className="sim-feedback sim-feedback--error" role="alert">
              {session.error}
            </p>
          )}
          <SimSummary session={session} />
          <div className="sim-grid">
            <EventComposer
              session={session}
              busy={sim.busy !== null}
              blocked={blocked}
              feedback={sim.feedback}
              onApply={(event) => void sim.apply(event)}
            />
            <SimExplanation session={session} />
          </div>
          <div className="sim-grid sim-grid--wide">
            <SimAllocation session={session} />
            <StepComparison session={session} />
          </div>
          <div className="sim-grid">
            <SimTimeline session={session} />
            <SimLedger session={session} />
          </div>
          <Panel
            title="This step's record"
            description="Identifiers a replay must reproduce. Timings are excluded from the outcome hash."
          >
            <dl className="sim-record">
              <div>
                <dt>Recommendation</dt>
                <dd>{POLICY_NAME[session.policy]}</dd>
              </div>
              <div>
                <dt>Snapshot</dt>
                <dd className="mono">{shortHash(session.current.snapshot_hash)}</dd>
              </div>
              <div>
                <dt>Outcome</dt>
                <dd className="mono">{shortHash(session.current.outcome_hash)}</dd>
              </div>
              <div>
                <dt>Event id</dt>
                <dd className="mono">{session.current.event_id ?? 'initial'}</dd>
              </div>
              <div>
                <dt>Solver</dt>
                <dd className="num">
                  seed {session.config.random_seed} · {formatInt(session.config.workers)} worker ·{' '}
                  {session.config.time_limit_s}s limit
                </dd>
              </div>
            </dl>
          </Panel>
        </>
      )}
    </div>
  );
}

export default function Simulate() {
  const { detail } = useDashboard();
  return (
    <ScenarioGate detail={detail}>
      {/* Keyed by scenario: switching scenario discards the session view entirely. */}
      {(d) => <Workspace key={d.scenario.scenario_id} detail={d} />}
    </ScenarioGate>
  );
}
