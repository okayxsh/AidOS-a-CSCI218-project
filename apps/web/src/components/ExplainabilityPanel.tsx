import type { AllocationCell, PolicyResult, ScenarioDetail, UrgencyAssessment } from '../api/types';
import { CATEGORY_TONE, LIMIT_LABEL, POLICY_SHORT } from '../lib/display';
import { formatInt, resourceById, zoneShortName } from '../lib/format';
import { Panel } from './ui/Panel';
import { StatusBadge } from './ui/StatusBadge';

interface ExplainabilityPanelProps {
  detail: ScenarioDetail;
  cell: AllocationCell | undefined;
  result?: PolicyResult;
  urgency?: UrgencyAssessment;
}

/**
 * Why one zone received what it did for one resource. Two sources are kept apart: the
 * fuzzy rules (how urgent the zone is) and the allocation constraints (what the plan could
 * give). Every sentence and number comes from the engine; nothing is generated here.
 */
export function ExplainabilityPanel({ detail, cell, result, urgency }: ExplainabilityPanelProps) {
  if (!cell) {
    return (
      <Panel
        title="Explanation"
        description="Select a cell in the matrix to see why it received what it did."
      >
        <p className="explain__empty">No cell selected.</p>
      </Panel>
    );
  }

  const zone = detail.scenario.zones.find((z) => z.id === cell.zone_id);
  const resource = resourceById(detail.scenario).get(cell.resource_id);
  const limit = LIMIT_LABEL[cell.limit];
  const policy = result ? POLICY_SHORT[result.policy_id] : 'FCFS';
  const stock = detail.scenario.stock[cell.resource_id] ?? 0;
  const used = result?.metrics?.allocated_by_resource[cell.resource_id];
  const coefficient = result?.solver?.coefficients[cell.zone_id]?.[cell.resource_id];

  return (
    <Panel
      title="Explanation"
      description={`${zoneShortName(zone?.name ?? cell.zone_id)} · ${resource?.label ?? cell.resource_id} · ${policy}`}
    >
      <section className="explain__part" aria-label="From the allocation constraints">
        <h3 className="explain__heading">From the allocation constraints</h3>
        <dl className="explain__figures">
          <div>
            <dt>Requested</dt>
            <dd className="num">{formatInt(cell.requested)}</dd>
          </div>
          <div>
            <dt>Allocated</dt>
            <dd className="num">{formatInt(cell.allocated)}</dd>
          </div>
          <div className={cell.unmet > 0 ? 'is-short' : undefined}>
            <dt>Unmet</dt>
            <dd className="num">{formatInt(cell.unmet)}</dd>
          </div>
        </dl>
        <p className="explain__limit">
          <StatusBadge tone={limit.tone}>{limit.label}</StatusBadge>
        </p>
        <p className="explain__reason">{cell.reason}</p>
        {used !== undefined && (
          <p className="explain__binding num">
            {resource?.label ?? cell.resource_id}: {formatInt(used)} of {formatInt(stock)} in stock
            allocated across all zones by this plan.
          </p>
        )}
      </section>

      {urgency && (
        <section className="explain__part" aria-label="From the fuzzy rules">
          <h3 className="explain__heading">From the fuzzy rules</h3>
          <p className="explain__score">
            <span className="num">{urgency.score.toFixed(1)}</span>
            <StatusBadge tone={CATEGORY_TONE[urgency.category]}>{urgency.category}</StatusBadge>
            {coefficient !== undefined && (
              <span className="explain__coef num">
                objective coefficient {formatInt(coefficient)}
              </span>
            )}
          </p>
          <ul className="urgency-rules">
            {urgency.activations.slice(0, 3).map((a) => (
              <li key={a.rule_id}>
                <span className="mono urgency-rules__id">{a.rule_id}</span>
                <span className="urgency-rules__text">{a.text}</span>
                <span className="num urgency-rules__pts">+{a.contribution.toFixed(1)}</span>
              </li>
            ))}
          </ul>
          {result?.policy_id === 'fcfs' && (
            <p className="explain__note">
              FCFS ignores urgency by design; the score is shown for reference.
            </p>
          )}
        </section>
      )}

      <p className="explain__source">
        Fuzzy scores weigh zones for urgency greedy and AidOS; they never relax a limit. The
        quantities come from the {policy} computation and the reason text is the engine&rsquo;s own.
      </p>
    </Panel>
  );
}
