import { RequestBar } from '../components/RequestBar';
import { SEGMENT_SHADES } from '../lib/display';
import { ScenarioGate, ScenarioHeader } from '../components/ScenarioGate';
import { Panel } from '../components/ui/Panel';
import type { ScenarioDetail } from '../api/types';
import { formatInt, resourceById, zoneShortName } from '../lib/format';
import { useDashboard } from '../state/dashboard';

function ResourceBoard({ detail }: { detail: ScenarioDetail }) {
  const resources = resourceById(detail.scenario);
  const active = detail.scenario.zones.filter(
    (z) => detail.summary.zones.find((s) => s.zone_id === z.id)?.active,
  );
  return (
    <Panel
      title="Requests by zone against stock"
      description="Each bar stacks the active zones' requests. Everything past the teal marker cannot be served by any policy."
    >
      <ul className="resource-board">
        {detail.summary.resources.map((r) => {
          const meta = resources.get(r.resource_id);
          return (
            <li key={r.resource_id}>
              <div className="resource-board__head">
                <h3>{meta?.label ?? r.resource_id}</h3>
                <span className="resource-board__nums num">
                  {formatInt(r.requested)} requested · {formatInt(r.stock)} in stock
                </span>
                {r.shortfall > 0 ? (
                  <span className="gap gap--short num">{formatInt(r.shortfall)} short</span>
                ) : (
                  <span className="gap gap--ok num">
                    {r.surplus > 0 ? `${formatInt(r.surplus)} spare` : 'Exact'}
                  </span>
                )}
              </div>
              <RequestBar
                label={meta?.label ?? r.resource_id}
                stock={r.stock}
                requested={r.requested}
                segments={active.map((z) => ({
                  key: z.id,
                  label: zoneShortName(z.name),
                  units: z.demand[r.resource_id] ?? 0,
                }))}
              />
            </li>
          );
        })}
      </ul>
      <ul className="request-legend">
        {active.map((z, i) => (
          <li key={z.id}>
            <i
              style={{ background: SEGMENT_SHADES[i % SEGMENT_SHADES.length] }}
              aria-hidden="true"
            />
            {zoneShortName(z.name)}
          </li>
        ))}
        <li>
          <i className="request-legend__stock" aria-hidden="true" />
          Depot stock
        </li>
      </ul>
    </Panel>
  );
}

function RequestMatrix({ detail }: { detail: ScenarioDetail }) {
  const zoneState = new Map(detail.summary.zones.map((z) => [z.zone_id, z]));
  return (
    <Panel
      title="Request matrix"
      description="Units requested per zone and resource, with the backend's totals."
    >
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Zone</th>
              {detail.scenario.resources.map((r) => (
                <th key={r.id} scope="col" className="is-num">
                  {r.label}
                </th>
              ))}
              <th scope="col" className="is-num">
                Total
              </th>
            </tr>
          </thead>
          <tbody>
            {detail.scenario.zones.map((z) => {
              const state = zoneState.get(z.id);
              return (
                <tr key={z.id} className={state?.active ? undefined : 'is-inactive'}>
                  <th scope="row">
                    {zoneShortName(z.name)}
                    {!state?.active && <span className="zone-place">Not active at this step</span>}
                  </th>
                  {detail.scenario.resources.map((r) => (
                    <td key={r.id} className="is-num num">
                      {formatInt(z.demand[r.id] ?? 0)}
                    </td>
                  ))}
                  <td className="is-num num">{formatInt(state?.requested_units ?? 0)}</td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr>
              <th scope="row">Requested by active zones</th>
              {detail.summary.resources.map((r) => (
                <td key={r.resource_id} className="is-num num">
                  {formatInt(r.requested)}
                </td>
              ))}
              <td className="is-num num">{formatInt(detail.summary.totals.requested)}</td>
            </tr>
            <tr>
              <th scope="row">Depot stock</th>
              {detail.summary.resources.map((r) => (
                <td key={r.resource_id} className="is-num num is-stock">
                  {formatInt(r.stock)}
                </td>
              ))}
              <td className="is-num num is-stock">{formatInt(detail.summary.totals.stock)}</td>
            </tr>
            <tr>
              <th scope="row">Shortfall</th>
              {detail.summary.resources.map((r) => (
                <td
                  key={r.resource_id}
                  className={`is-num num${r.shortfall > 0 ? ' is-short' : ''}`}
                >
                  {formatInt(r.shortfall)}
                </td>
              ))}
              <td className={`is-num num${detail.summary.totals.shortfall > 0 ? ' is-short' : ''}`}>
                {formatInt(detail.summary.totals.shortfall)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </Panel>
  );
}

export default function Inventory() {
  const { detail } = useDashboard();
  return (
    <ScenarioGate detail={detail}>
      {(d) => (
        <div className="page" key={d.snapshot_hash}>
          <ScenarioHeader detail={d} title="Resource inventory" />
          <ResourceBoard detail={d} />
          <RequestMatrix detail={d} />
        </div>
      )}
    </ScenarioGate>
  );
}
