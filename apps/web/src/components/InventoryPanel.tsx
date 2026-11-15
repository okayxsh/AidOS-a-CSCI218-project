import type { ScenarioDetail } from '../api/types';
import { formatInt, resourceById, resourceColour } from '../lib/format';
import { Panel } from './ui/Panel';

/** Depot stock against active requests, per resource, exactly as the backend summarised it. */
export function InventoryPanel({ detail }: { detail: ScenarioDetail }) {
  const resources = resourceById(detail.scenario);
  return (
    <Panel title="Resource inventory" description="Depot stock against requests from active zones.">
      <div className="table-scroll">
        <table className="data-table inventory-table">
          <thead>
            <tr>
              <th scope="col">Resource</th>
              <th scope="col" className="is-num">
                In stock
              </th>
              <th scope="col" className="is-num">
                Requested
              </th>
              <th scope="col" className="is-num">
                Gap
              </th>
            </tr>
          </thead>
          <tbody>
            {detail.summary.resources.map((r, i) => {
              const meta = resources.get(r.resource_id);
              const ratio = r.requested === 0 ? 1 : Math.min(1, r.stock / r.requested);
              return (
                <tr key={r.resource_id}>
                  <th scope="row">
                    <span className="resource-name">
                      <i
                        style={{ background: resourceColour(r.resource_id, i) }}
                        aria-hidden="true"
                      />
                      {meta?.label ?? r.resource_id}
                    </span>
                    <span className="cover-track" aria-hidden="true">
                      <span style={{ width: `${ratio * 100}%` }} />
                    </span>
                  </th>
                  <td className="is-num num" data-label="In stock">
                    {formatInt(r.stock)}
                  </td>
                  <td className="is-num num" data-label="Requested">
                    {formatInt(r.requested)}
                  </td>
                  <td className="is-num num" data-label="Gap">
                    {r.shortfall > 0 ? (
                      <span className="gap gap--short">{formatInt(r.shortfall)} short</span>
                    ) : (
                      <span className="gap gap--ok">
                        {r.surplus > 0 ? `${formatInt(r.surplus)} spare` : 'Exact'}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
