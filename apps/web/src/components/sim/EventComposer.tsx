import { Send } from 'lucide-react';
import { useId, useState, type FormEvent } from 'react';
import type { CrisisZone, SimEvent, SimEventType, SimSession } from '../../api/types';
import { formatInt, zoneShortName } from '../../lib/format';
import { EVENT_LABEL, EVENT_ORDER, POLICY_NAME } from '../../lib/simulation';
import type { SimFeedback } from '../../state/simulation';
import { Panel } from '../ui/Panel';

const RATINGS = ['severity', 'vulnerability', 'time_criticality'] as const;
type Rating = (typeof RATINGS)[number];
const RATING_LABEL: Record<Rating, string> = {
  severity: 'Severity',
  vulnerability: 'Vulnerability',
  time_criticality: 'Time criticality',
};
const ID_PATTERN = /^[a-z0-9][a-z0-9_-]*$/;

interface EventComposerProps {
  session: SimSession;
  busy: boolean;
  /** Why events cannot be applied right now (e.g. the session is paused), if so. */
  blocked: string | null;
  feedback: SimFeedback | null;
  onApply: (event: SimEvent) => void;
}

const isInt = (text: string) => /^\d+$/.test(text.trim());
const asRating = (text: string) => {
  const value = Number(text);
  return text.trim() !== '' && Number.isFinite(value) && value >= 0 && value <= 10 ? value : null;
};

function NumberField(props: {
  id: string;
  label: string;
  value: string;
  min: number;
  max?: number;
  step?: number;
  onChange: (value: string) => void;
}) {
  return (
    <div className="field">
      <label htmlFor={props.id}>{props.label}</label>
      <input
        id={props.id}
        type="number"
        inputMode="decimal"
        min={props.min}
        max={props.max}
        step={props.step ?? 1}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
      />
    </div>
  );
}

function nextZoneId(taken: Set<string>): string {
  for (const letter of 'abcdefghijklmnopqrstuvwxyz') {
    if (!taken.has(`zone-${letter}`)) return `zone-${letter}`;
  }
  return `zone-${taken.size + 1}`;
}

/**
 * Compose one crisis event. Only clearly invalid input is blocked here; the engine checks
 * every event against the current scenario and its message is shown when it refuses.
 */
export function EventComposer({ session, busy, blocked, feedback, onApply }: EventComposerProps) {
  const uid = useId();
  const scenario = session.current.scenario;
  const zones = scenario.zones;
  const resources = scenario.resources;
  const [type, setType] = useState<SimEventType>('urgency_changed');
  const [pickedZone, setPickedZone] = useState(zones[0]?.id ?? '');
  const [pickedResource, setPickedResource] = useState(resources[0]?.id ?? '');
  const zone: CrisisZone | undefined = zones.find((z) => z.id === pickedZone) ?? zones[0];
  const resourceId = resources.some((r) => r.id === pickedResource)
    ? pickedResource
    : (resources[0]?.id ?? '');
  const resourceLabel = resources.find((r) => r.id === resourceId)?.label ?? resourceId;

  // Edits belong to one context; changing the event, zone, resource or session version
  // drops them, so every form opens on the engine's current values.
  const context = `${session.version}|${type}|${zone?.id}|${resourceId}`;
  const [edits, setEdits] = useState<{ at: string; values: Record<string, string> }>({
    at: '',
    values: {},
  });
  const values = edits.at === context ? edits.values : {};
  const set = (key: string, value: string) =>
    setEdits((prev) => ({
      at: context,
      values: { ...(prev.at === context ? prev.values : {}), [key]: value },
    }));

  const taken = new Set([
    ...zones.map((z) => z.id),
    ...session.resolved_zones.map((r) => r.zone_id),
  ]);
  const suggestedId = nextZoneId(taken);
  const newId = values['nz.id'] ?? suggestedId;
  const letter = newId.replace(/^zone-/, '').toUpperCase();
  const newName = values['nz.name'] ?? `Zone ${letter} · New report`;

  const recommended = session.current.comparison.results.find(
    (r) => r.policy_id === session.policy,
  );
  const planUnits = recommended?.metrics?.allocated_units ?? 0;
  const stock = scenario.stock[resourceId] ?? 0;
  const currentDemand = zone?.demand[resourceId] ?? 0;
  const scheduled = zones.filter((z) => z.activation_step === scenario.step + 1);

  const build = (): { event: SimEvent | null; problem: string | null } => {
    switch (type) {
      case 'urgency_changed': {
        if (!zone) return { event: null, problem: 'Choose a zone.' };
        const changed: Partial<Record<Rating, number>> = {};
        for (const r of RATINGS) {
          const value = asRating(values[r] ?? String(zone[r]));
          if (value === null) return { event: null, problem: 'Ratings are numbers from 0 to 10.' };
          if (value !== zone[r]) changed[r] = value;
        }
        if (Object.keys(changed).length === 0)
          return { event: null, problem: 'Change at least one rating.' };
        return { event: { type, zone_id: zone.id, ...changed }, problem: null };
      }
      case 'zone_added': {
        if (!ID_PATTERN.test(newId) || newId.length > 64)
          return { event: null, problem: 'The id uses lower-case letters, digits, - or _.' };
        if (taken.has(newId)) return { event: null, problem: `The id ${newId} is already used.` };
        if (!newName.trim()) return { event: null, problem: 'Give the zone a name.' };
        const ratings: Partial<Record<Rating, number>> = {};
        for (const r of RATINGS) {
          const value = asRating(values[`nz.${r}`] ?? '8');
          if (value === null) return { event: null, problem: 'Ratings are numbers from 0 to 10.' };
          ratings[r] = value;
        }
        const demand: Record<string, number> = {};
        for (const res of resources) {
          const text = values[`nz.demand.${res.id}`] ?? '20';
          if (!isInt(text)) return { event: null, problem: 'Requests are whole units, 0 or more.' };
          demand[res.id] = Number(text);
        }
        return {
          event: {
            type,
            zone: {
              id: newId,
              name: newName.trim(),
              severity: ratings.severity as number,
              vulnerability: ratings.vulnerability as number,
              time_criticality: ratings.time_criticality as number,
              demand,
            },
          },
          problem: null,
        };
      }
      case 'supply_arrived':
      case 'supply_lost': {
        const text = values.quantity ?? '';
        if (!isInt(text) || Number(text) < 1)
          return { event: null, problem: 'Enter a whole number of units, at least 1.' };
        if (type === 'supply_lost' && Number(text) > stock)
          return {
            event: null,
            problem: `Only ${formatInt(stock)} in stock: stock never goes negative.`,
          };
        return { event: { type, resource_id: resourceId, quantity: Number(text) }, problem: null };
      }
      case 'request_updated': {
        if (!zone) return { event: null, problem: 'Choose a zone.' };
        const text = values.quantity ?? String(currentDemand);
        if (!isInt(text)) return { event: null, problem: 'Requests are whole units, 0 or more.' };
        if (Number(text) === currentDemand)
          return { event: null, problem: `Already requesting ${formatInt(currentDemand)}.` };
        return {
          event: { type, zone_id: zone.id, resource_id: resourceId, quantity: Number(text) },
          problem: null,
        };
      }
      case 'zone_resolved':
        if (!zone) return { event: null, problem: 'Choose a zone.' };
        if (zones.length === 1)
          return { event: null, problem: 'The last zone cannot be resolved.' };
        return { event: { type, zone_id: zone.id }, problem: null };
      case 'time_advanced':
        return { event: { type }, problem: null };
      case 'plan_committed':
        if (planUnits === 0)
          return { event: null, problem: 'The current plan dispatches no units.' };
        return {
          event: {
            type,
            policy: session.policy,
            expected_snapshot_hash: session.current.snapshot_hash,
          },
          problem: null,
        };
    }
  };

  const { event, problem } = build();
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (event && !blocked && !busy) onApply(event);
  };
  const error = feedback?.source === 'event' && feedback.tone === 'error' ? feedback : null;
  const needsZone = ['urgency_changed', 'request_updated', 'zone_resolved'].includes(type);
  const needsResource = ['supply_arrived', 'supply_lost', 'request_updated'].includes(type);

  return (
    <Panel
      title="Apply an event"
      description="A hypothetical change to the synthetic scenario. The engine validates it, rescores urgency and re-runs every policy."
    >
      <form className="sim-form" onSubmit={submit} aria-describedby={`${uid}-hint`}>
        <div className="field field--wide">
          <label htmlFor={`${uid}-type`}>Event</label>
          <select
            id={`${uid}-type`}
            value={type}
            onChange={(e) => setType(e.target.value as SimEventType)}
          >
            {EVENT_ORDER.map((t) => (
              <option key={t} value={t}>
                {EVENT_LABEL[t]}
              </option>
            ))}
          </select>
        </div>

        {needsZone && (
          <div className="field field--wide">
            <label htmlFor={`${uid}-zone`}>Zone</label>
            <select
              id={`${uid}-zone`}
              value={zone?.id ?? ''}
              onChange={(e) => setPickedZone(e.target.value)}
            >
              {zones.map((z) => (
                <option key={z.id} value={z.id}>
                  {zoneShortName(z.name)}
                  {z.activation_step > scenario.step
                    ? ` (scheduled for step ${z.activation_step})`
                    : ''}
                </option>
              ))}
            </select>
          </div>
        )}

        {needsResource && (
          <div className="field field--wide">
            <label htmlFor={`${uid}-resource`}>Resource</label>
            <select
              id={`${uid}-resource`}
              value={resourceId}
              onChange={(e) => setPickedResource(e.target.value)}
            >
              {resources.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {type === 'urgency_changed' &&
          zone &&
          RATINGS.map((r) => (
            <NumberField
              key={r}
              id={`${uid}-${r}`}
              label={`${RATING_LABEL[r]} (now ${zone[r]})`}
              value={values[r] ?? String(zone[r])}
              min={0}
              max={10}
              step={0.5}
              onChange={(v) => set(r, v)}
            />
          ))}

        {type === 'zone_added' && (
          <>
            <div className="field">
              <label htmlFor={`${uid}-nz-id`}>Zone id</label>
              <input
                id={`${uid}-nz-id`}
                value={newId}
                onChange={(e) => set('nz.id', e.target.value)}
                spellCheck={false}
              />
            </div>
            <div className="field">
              <label htmlFor={`${uid}-nz-name`}>Name</label>
              <input
                id={`${uid}-nz-name`}
                value={newName}
                maxLength={80}
                onChange={(e) => set('nz.name', e.target.value)}
              />
            </div>
            {RATINGS.map((r) => (
              <NumberField
                key={r}
                id={`${uid}-nz-${r}`}
                label={RATING_LABEL[r]}
                value={values[`nz.${r}`] ?? '8'}
                min={0}
                max={10}
                step={0.5}
                onChange={(v) => set(`nz.${r}`, v)}
              />
            ))}
            {resources.map((res) => (
              <NumberField
                key={res.id}
                id={`${uid}-nz-${res.id}`}
                label={`${res.label} requested`}
                value={values[`nz.demand.${res.id}`] ?? '20'}
                min={0}
                onChange={(v) => set(`nz.demand.${res.id}`, v)}
              />
            ))}
          </>
        )}

        {(type === 'supply_arrived' || type === 'supply_lost') && (
          <NumberField
            id={`${uid}-qty`}
            label={`Units ${type === 'supply_arrived' ? 'arriving' : 'lost'} (in stock: ${formatInt(stock)})`}
            value={values.quantity ?? ''}
            min={1}
            max={type === 'supply_lost' ? stock : undefined}
            onChange={(v) => set('quantity', v)}
          />
        )}

        {type === 'request_updated' && zone && (
          <NumberField
            id={`${uid}-qty`}
            label={`New request for ${resourceLabel.toLowerCase()} (now ${formatInt(currentDemand)})`}
            value={values.quantity ?? String(currentDemand)}
            min={0}
            onChange={(v) => set('quantity', v)}
          />
        )}

        <div className="sim-form__note field--wide">
          {type === 'zone_added' && (
            <p>The new zone arrives after every existing zone, so FCFS serves it last.</p>
          )}
          {type === 'zone_resolved' && (
            <p>
              The zone leaves the allocation problem with its open requests. Units already
              dispatched to it stay dispatched; nothing returns to the depot.
            </p>
          )}
          {type === 'time_advanced' && (
            <p>
              The clock moves from step {scenario.step} to {scenario.step + 1}.{' '}
              {scheduled.length
                ? `${scheduled.map((z) => zoneShortName(z.name)).join(', ')} ${scheduled.length === 1 ? 'is' : 'are'} scheduled to report then.`
                : 'No zone is scheduled for that step, so only the clock changes.'}
            </p>
          )}
          {type === 'plan_committed' && (
            <p>
              Dispatches the current {POLICY_NAME[session.policy]} plan:{' '}
              <b className="num">{formatInt(planUnits)}</b> units leave the depot. Stock and the
              receiving zones&apos; open requests drop by exactly those units, and the dispatch is
              written once to the ledger. Only a reset undoes it. The engine refuses it if the plan
              is stale.
            </p>
          )}
        </div>

        <div className="sim-form__actions field--wide">
          <button
            type="submit"
            className="btn btn--accent"
            disabled={Boolean(problem) || Boolean(blocked) || busy}
          >
            <Send size={15} aria-hidden="true" />
            {type === 'plan_committed' ? 'Dispatch plan' : 'Apply event'}
          </button>
          <p id={`${uid}-hint`} className="sim-form__hint" aria-live="polite">
            {blocked ?? problem ?? ''}
          </p>
        </div>
        {error && (
          <p className="sim-form__error field--wide" role="alert">
            The engine refused this event: {error.message}
          </p>
        )}
      </form>
    </Panel>
  );
}
