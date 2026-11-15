import type { ScenarioDetail, UrgencyAssessment } from '../api/types';
import { CATEGORY_TONE, INPUT_LABEL } from '../lib/display';
import { formatRating, zoneShortName } from '../lib/format';
import { Panel } from './ui/Panel';
import { StatusBadge } from './ui/StatusBadge';

interface UrgencyPanelProps {
  detail: ScenarioDetail;
  zones: UrgencyAssessment[] | undefined;
  status: 'idle' | 'loading' | 'success' | 'error';
  method?: string;
}

const TERMS = ['low', 'medium', 'high'] as const;

/** Fuzzy urgency per zone, exactly as the engine scored it, with the rules behind each score. */
export function UrgencyPanel({ detail, zones, status, method }: UrgencyPanelProps) {
  const names = new Map(detail.scenario.zones.map((z) => [z.id, z.name]));
  const ranked = [...(zones ?? [])].sort((a, b) => b.score - a.score);

  return (
    <Panel
      title="Fuzzy urgency"
      description="Zero-order Sugeno inference over severity, time-criticality and vulnerability. Each rule's contribution adds up to the score (0–100). Scores are simulation inputs, not triage grades."
    >
      {status === 'loading' && !zones && <p className="explain__empty">Scoring zones…</p>}
      {status === 'error' && !zones && (
        <p className="explain__empty">
          Urgency scores are unavailable: the engine did not respond.
        </p>
      )}
      {zones && (
        <ol className="urgency-list">
          {ranked.map((u) => {
            const id = u.zone_id ?? '';
            const top = u.activations.slice(0, 2);
            return (
              <li key={id} className={u.active === false ? 'is-inactive' : undefined}>
                <div className="urgency-row">
                  <span className="urgency-row__zone">{zoneShortName(names.get(id) ?? id)}</span>
                  <span className="urgency-row__track" aria-hidden="true">
                    <span style={{ width: `${u.score}%` }} />
                  </span>
                  <span className="urgency-row__score num">{u.score.toFixed(1)}</span>
                  <StatusBadge tone={CATEGORY_TONE[u.category]}>{u.category}</StatusBadge>
                </div>
                <ul className="urgency-rules">
                  {top.map((a) => (
                    <li key={a.rule_id}>
                      <span className="mono urgency-rules__id">{a.rule_id}</span>
                      <span className="urgency-rules__text">{a.text}</span>
                      <span className="num urgency-rules__pts">
                        +{a.contribution.toFixed(1)}
                        <span className="visually-hidden"> points</span>
                      </span>
                    </li>
                  ))}
                </ul>
                <details className="urgency-details">
                  <summary>
                    Memberships and all {u.activations.length} fired rule
                    {u.activations.length === 1 ? '' : 's'}
                  </summary>
                  <table className="data-table urgency-memberships">
                    <caption className="visually-hidden">
                      Membership degree of each rating in each linguistic set
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Rating</th>
                        <th scope="col" className="is-num">
                          Value
                        </th>
                        {TERMS.map((t) => (
                          <th key={t} scope="col" className="is-num">
                            {t}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Object.keys(u.memberships).map((name) => (
                        <tr key={name}>
                          <th scope="row">{INPUT_LABEL[name] ?? name}</th>
                          <td className="is-num num">{formatRating(u.inputs[name])}</td>
                          {TERMS.map((t) => (
                            <td key={t} className="is-num num">
                              {(u.memberships[name][t] ?? 0).toFixed(2)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <ul className="urgency-rules urgency-rules--all">
                    {u.activations.map((a) => (
                      <li key={a.rule_id}>
                        <span className="mono urgency-rules__id">{a.rule_id}</span>
                        <span className="urgency-rules__text">
                          {a.text}{' '}
                          <span className="urgency-rules__meta num">
                            strength {a.strength.toFixed(2)} × {a.output}
                          </span>
                        </span>
                        <span className="num urgency-rules__pts">+{a.contribution.toFixed(1)}</span>
                      </li>
                    ))}
                  </ul>
                  <p className="explain__source">{u.explanation}</p>
                </details>
              </li>
            );
          })}
        </ol>
      )}
      {method && <p className="urgency-method mono">{method}</p>}
    </Panel>
  );
}
