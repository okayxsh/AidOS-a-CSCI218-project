import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { CrisisZone, ScenarioDetail, UrgencyAssessment } from '../api/types';
import { CATEGORY_TONE } from '../lib/display';
import { formatInt, formatRating, zonePlaceName, zoneShortName } from '../lib/format';
import { useUrgency } from '../state/scenario';
import { Panel } from './ui/Panel';
import { StatusBadge } from './ui/StatusBadge';

type SortKey =
  | 'arrival'
  | 'name'
  | 'severity'
  | 'vulnerability'
  | 'time'
  | 'urgency'
  | 'population'
  | 'requested';

interface Row {
  zone: CrisisZone;
  active: boolean;
  requested: number;
  urgency: UrgencyAssessment | undefined;
}

const ACCESSORS: Record<SortKey, (r: Row) => number | string> = {
  arrival: (r) => r.zone.arrival_order,
  name: (r) => r.zone.name,
  severity: (r) => r.zone.severity,
  vulnerability: (r) => r.zone.vulnerability,
  time: (r) => r.zone.time_criticality,
  urgency: (r) => r.urgency?.score ?? -1,
  population: (r) => r.zone.population ?? -1,
  requested: (r) => r.requested,
};

// Text-first columns sort ascending on first click; ratings and quantities descending.
const DEFAULT_DIR: Record<SortKey, 'asc' | 'desc'> = {
  arrival: 'asc',
  name: 'asc',
  severity: 'desc',
  vulnerability: 'desc',
  time: 'desc',
  urgency: 'desc',
  population: 'desc',
  requested: 'desc',
};

function Rating({ value }: { value: number }) {
  return (
    <span className="rating">
      <span className="rating__track" aria-hidden="true">
        <span style={{ width: `${value * 10}%` }} />
      </span>
      <span className="num">{formatRating(value)}</span>
    </span>
  );
}

/** All zones in the snapshot with their simulated ratings and backend-summed requests. */
export function ZoneTable({ detail }: { detail: ScenarioDetail }) {
  const urgency = useUrgency(detail);
  const [sort, setSort] = useState<{ key: SortKey; dir: 'asc' | 'desc' }>({
    key: 'arrival',
    dir: 'asc',
  });

  const rows = useMemo(() => {
    const summaries = new Map(detail.summary.zones.map((z) => [z.zone_id, z]));
    const scores = new Map(urgency.data?.zones.map((u) => [u.zone_id, u]));
    const list: Row[] = detail.scenario.zones.map((zone) => ({
      zone,
      active: summaries.get(zone.id)?.active ?? false,
      requested: summaries.get(zone.id)?.requested_units ?? 0,
      urgency: scores.get(zone.id),
    }));
    const get = ACCESSORS[sort.key];
    return list.sort((a, b) => {
      const x = get(a);
      const y = get(b);
      const order = typeof x === 'string' ? x.localeCompare(String(y)) : x - (y as number);
      // Ties fall back to arrival order, then ID, so the table is deterministic.
      const tie = a.zone.arrival_order - b.zone.arrival_order || a.zone.id.localeCompare(b.zone.id);
      return (sort.dir === 'asc' ? order : -order) || tie;
    });
  }, [detail, sort, urgency.data]);

  const header = (key: SortKey, label: string, numeric = false) => {
    const current = sort.key === key;
    const Icon = !current ? ArrowUpDown : sort.dir === 'asc' ? ArrowUp : ArrowDown;
    return (
      <th
        scope="col"
        className={numeric ? 'is-num' : undefined}
        aria-sort={current ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}
      >
        <button
          type="button"
          className="sort-button"
          onClick={() =>
            setSort((s) =>
              s.key === key
                ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' }
                : { key, dir: DEFAULT_DIR[key] },
            )
          }
        >
          {label}
          <Icon size={13} aria-hidden="true" />
        </button>
      </th>
    );
  };

  const activeCount = rows.filter((r) => r.active).length;

  return (
    <Panel
      title="Emergency zones"
      description={`${activeCount} of ${rows.length} zones active at step ${detail.scenario.step}. Ratings are simulated inputs (0–10), not triage grades; urgency is the engine's fuzzy score (0–100).`}
    >
      <div className="table-scroll">
        <table className="data-table zone-table">
          <thead>
            <tr>
              {header('name', 'Zone')}
              {header('arrival', 'Arrival', true)}
              {header('severity', 'Severity')}
              {header('vulnerability', 'Vulnerability')}
              {header('time', 'Time-criticality')}
              {header('urgency', 'Urgency', true)}
              {header('population', 'Population', true)}
              {header('requested', 'Units requested', true)}
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ zone, active, requested, urgency: score }) => (
              <tr key={zone.id} className={active ? undefined : 'is-inactive'}>
                <th scope="row">
                  <span className="zone-name">{zoneShortName(zone.name)}</span>
                  {zonePlaceName(zone.name) && (
                    <span className="zone-place">{zonePlaceName(zone.name)}</span>
                  )}
                </th>
                <td className="is-num num">{zone.arrival_order}</td>
                <td>
                  <Rating value={zone.severity} />
                </td>
                <td>
                  <Rating value={zone.vulnerability} />
                </td>
                <td>
                  <Rating value={zone.time_criticality} />
                </td>
                <td className="is-num">
                  {score ? (
                    <span className="zone-urgency">
                      <span className="num">{score.score.toFixed(1)}</span>
                      <StatusBadge tone={CATEGORY_TONE[score.category]}>
                        {score.category}
                      </StatusBadge>
                    </span>
                  ) : (
                    <span className="zone-urgency__none">
                      {urgency.status === 'loading' ? 'Scoring…' : 'N/A'}
                    </span>
                  )}
                </td>
                <td className="is-num num">
                  {zone.population === null ? '—' : formatInt(zone.population)}
                </td>
                <td className="is-num num">{formatInt(requested)}</td>
                <td>
                  {active ? (
                    <StatusBadge tone="ok" dot>
                      Active
                    </StatusBadge>
                  ) : (
                    <StatusBadge tone="planned">
                      Activates at step {zone.activation_step}
                    </StatusBadge>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
