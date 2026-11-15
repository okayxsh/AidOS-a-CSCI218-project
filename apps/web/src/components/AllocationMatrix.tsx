import type { AllocationCell, PolicyResult, ScenarioDetail } from '../api/types';
import { LIMIT_LABEL } from '../lib/display';
import { formatInt, formatRatio, resourceById, zoneShortName } from '../lib/format';

export interface CellKey {
  zoneId: string;
  resourceId: string;
}

interface AllocationMatrixProps {
  detail: ScenarioDetail;
  result: PolicyResult;
  selected: CellKey | null;
  onSelect: (key: CellKey) => void;
}

/** Zones (in the order the policy served them) by resources. Every value is from the backend. */
export function AllocationMatrix({ detail, result, selected, onSelect }: AllocationMatrixProps) {
  const resources = resourceById(detail.scenario);
  const zones = new Map(detail.scenario.zones.map((z) => [z.id, z]));
  const cells = new Map(result.cells.map((c) => [`${c.zone_id}|${c.resource_id}`, c]));
  const resourceIds = detail.scenario.resources.map((r) => r.id);

  return (
    <div className="table-scroll">
      <table className="data-table matrix">
        <caption className="visually-hidden">
          Units allocated by the {result.label} policy, per zone and resource. Select a cell for its
          explanation.
        </caption>
        <thead>
          <tr>
            <th scope="col">Zone · order</th>
            {resourceIds.map((rid) => (
              <th key={rid} scope="col">
                {resources.get(rid)?.label ?? rid}
              </th>
            ))}
            <th scope="col" className="is-num">
              Coverage
            </th>
          </tr>
        </thead>
        <tbody>
          {result.zone_order.map((zoneId, index) => (
            <tr key={zoneId}>
              <th scope="row">
                <span className="matrix__order num">{index + 1}</span>
                {zoneShortName(zones.get(zoneId)?.name ?? zoneId)}
              </th>
              {resourceIds.map((rid) => {
                const cell = cells.get(`${zoneId}|${rid}`);
                if (!cell) return <td key={rid} />;
                return (
                  <td key={rid} className="matrix__cell-wrap">
                    <MatrixCell
                      cell={cell}
                      zoneLabel={zoneShortName(zones.get(zoneId)?.name ?? zoneId)}
                      resourceLabel={resources.get(rid)?.label ?? rid}
                      selected={selected?.zoneId === zoneId && selected?.resourceId === rid}
                      onSelect={() => onSelect({ zoneId, resourceId: rid })}
                    />
                  </td>
                );
              })}
              <td className="is-num num">
                {formatRatio(result.metrics?.coverage_by_zone[zoneId])}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">Resource coverage</th>
            {resourceIds.map((rid) => (
              <td key={rid} className="num">
                {formatRatio(result.metrics?.coverage_by_resource[rid])}
              </td>
            ))}
            <td className="is-num num">{formatRatio(result.metrics?.unit_coverage)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

interface MatrixCellProps {
  cell: AllocationCell;
  zoneLabel: string;
  resourceLabel: string;
  selected: boolean;
  onSelect: () => void;
}

function MatrixCell({ cell, zoneLabel, resourceLabel, selected, onSelect }: MatrixCellProps) {
  const ratio = cell.requested === 0 ? 0 : cell.allocated / cell.requested;
  return (
    <button
      type="button"
      className={`matrix__cell matrix__cell--${cell.limit}`}
      aria-pressed={selected}
      aria-label={`${zoneLabel}, ${resourceLabel}: ${cell.allocated} of ${cell.requested} allocated. ${LIMIT_LABEL[cell.limit].label}.`}
      onClick={onSelect}
    >
      {cell.requested === 0 ? (
        <span className="matrix__none">—</span>
      ) : (
        <>
          <span className="matrix__nums num">
            <b>{formatInt(cell.allocated)}</b>
            <span>/ {formatInt(cell.requested)}</span>
          </span>
          <span className="matrix__bar" aria-hidden="true">
            <span style={{ width: `${ratio * 100}%` }} />
          </span>
        </>
      )}
    </button>
  );
}
