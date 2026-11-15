import {
  Gauge,
  GitBranch,
  ListChecks,
  Scale,
  ShieldCheck,
  Waypoints,
  type LucideIcon,
} from 'lucide-react';
import { useId, useRef, useState, type KeyboardEvent, type ReactNode } from 'react';
import { demoResources, demoZones } from '../content/demoScenario';
import { STATUS_LABEL, type BuildStatus } from '../content/landing';
import { formatInt, formatRating, zoneShortName } from '../lib/format';
import { SectionHeading } from './ui/SectionHeading';
import { StatusBadge } from './ui/StatusBadge';

interface Feature {
  key: string;
  icon: LucideIcon;
  title: string;
  summary: string;
  status: BuildStatus;
  stage: string;
  panel: () => ReactNode;
}

const FEATURES: Feature[] = [
  {
    key: 'urgency',
    icon: Gauge,
    title: 'Intelligent urgency assessment',
    summary: 'Three imprecise ratings per zone become one explainable urgency score.',
    status: 'built',
    stage: 'Stage 2',
    panel: UrgencyPanel,
  },
  {
    key: 'constraints',
    icon: Scale,
    title: 'Constraint-aware allocation',
    summary: 'Whole units, never above a request, never above stock, no substitution.',
    status: 'built',
    stage: 'CP-SAT + two baselines',
    panel: ConstraintPanel,
  },
  {
    key: 'simulation',
    icon: GitBranch,
    title: 'Dynamic crisis simulation',
    summary: 'Inject events and watch the snapshot, and the plan, change.',
    status: 'built',
    stage: 'Stage 3 · 8 event types',
    panel: SimulationPanel,
  },
  {
    key: 'explanations',
    icon: ListChecks,
    title: 'Explainable recommendations',
    summary: 'Each allocation states which limit stopped it.',
    status: 'built',
    stage: 'Rule traces + reasons',
    panel: ExplanationPanel,
  },
  {
    key: 'comparison',
    icon: Waypoints,
    title: 'Allocation comparison',
    summary: 'Same scenario, same constraints, same metrics for every policy.',
    status: 'built',
    stage: 'Live comparison · offline evaluation runs',
    panel: ComparisonPanel,
  },
  {
    key: 'oversight',
    icon: ShieldCheck,
    title: 'Human oversight',
    summary: 'AidOS proposes. Stock moves only when a coordinator commits.',
    status: 'built',
    stage: 'Dispatch ledger · Stage 3',
    panel: OversightPanel,
  },
];

export function FeatureExplorer() {
  const [active, setActive] = useState(0);
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);
  const baseId = useId();
  const feature = FEATURES[active];

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const keys: Record<string, number> = {
      ArrowDown: 1,
      ArrowRight: 1,
      ArrowUp: -1,
      ArrowLeft: -1,
    };
    let next: number | null = null;
    if (event.key in keys) next = (active + keys[event.key] + FEATURES.length) % FEATURES.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = FEATURES.length - 1;
    if (next === null) return;
    event.preventDefault();
    setActive(next);
    tabs.current[next]?.focus();
  };

  return (
    <section id="features" className="section features" aria-labelledby="features-title">
      <div className="container">
        <SectionHeading
          id="features-title"
          title="What you can do with it"
          lede="Pick a capability to see what it shows. Each one is marked with its real build status."
        />
        <div className="features__layout">
          <div className="features__tabs" role="tablist" aria-label="AidOS capabilities">
            {FEATURES.map((f, i) => {
              const Icon = f.icon;
              const selected = i === active;
              return (
                <button
                  key={f.key}
                  ref={(el) => {
                    tabs.current[i] = el;
                  }}
                  id={`${baseId}-tab-${f.key}`}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  aria-controls={`${baseId}-panel`}
                  tabIndex={selected ? 0 : -1}
                  className="feature-tab"
                  onClick={() => setActive(i)}
                  onKeyDown={onKeyDown}
                >
                  <span className="feature-tab__icon" aria-hidden="true">
                    <Icon size={18} strokeWidth={1.75} />
                  </span>
                  <span className="feature-tab__text">
                    <span className="feature-tab__title">{f.title}</span>
                    <span className="feature-tab__summary">{f.summary}</span>
                  </span>
                </button>
              );
            })}
          </div>

          <div
            id={`${baseId}-panel`}
            role="tabpanel"
            aria-labelledby={`${baseId}-tab-${feature.key}`}
            className="feature-panel"
            tabIndex={0}
          >
            <div className="feature-panel__head">
              <h3>{feature.title}</h3>
              <span className="feature-panel__status">
                <StatusBadge tone={feature.status}>{STATUS_LABEL[feature.status]}</StatusBadge>
                <span>{feature.stage}</span>
              </span>
            </div>
            <div className="feature-panel__body" key={feature.key}>
              {feature.panel()}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ panels */

function UrgencyPanel() {
  const ratings = [
    { key: 'severity', label: 'Severity' },
    { key: 'vulnerability', label: 'Vulnerability' },
    { key: 'timeCriticality', label: 'Time-criticality' },
  ] as const;
  return (
    <div className="fp-urgency">
      <p className="fp-note">Inputs from the synthetic demo scenario, each rated 0–10.</p>
      <ul className="fp-urgency__zones">
        {demoZones.map((z) => (
          <li key={z.id}>
            <p className="fp-urgency__zone">{zoneShortName(z.name)}</p>
            <dl>
              {ratings.map((r) => (
                <div key={r.key} className="fp-meter">
                  <dt>{r.label}</dt>
                  <dd>
                    <span className="fp-meter__track">
                      <span style={{ width: `${z[r.key] * 10}%` }} />
                    </span>
                    <span className="num">{formatRating(z[r.key])}</span>
                  </dd>
                </div>
              ))}
            </dl>
            <p className="fp-urgency__score">
              Urgency score <span>computed live by the fuzzy engine in the dashboard</span>
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ConstraintPanel() {
  return (
    <div className="fp-matrix">
      <p className="fp-note">
        Requested units per zone. Every allocation must fit inside both limits.
      </p>
      <div className="fp-matrix__scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Zone</th>
              {demoResources.map((r) => (
                <th key={r.id} scope="col">
                  {r.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {demoZones.map((z) => (
              <tr key={z.id}>
                <th scope="row">{zoneShortName(z.name)}</th>
                {demoResources.map((r) => (
                  <td key={r.id} className="num">
                    {formatInt(z.demand[r.id] ?? 0)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th scope="row">Depot stock</th>
              {demoResources.map((r) => (
                <td key={r.id} className="num">
                  {formatInt(r.stock)}
                </td>
              ))}
            </tr>
          </tfoot>
        </table>
      </div>
      <ul className="fp-rules mono">
        <li>0 ≤ allocated ≤ requested, per cell</li>
        <li>Σ allocated ≤ stock, per column</li>
        <li>whole units only; columns never mix</li>
      </ul>
    </div>
  );
}

function SimulationPanel() {
  const events = [
    { type: 'supply_lost', text: 'Medical kits at the depot drop from 90 to 60' },
    { type: 'zone_added', text: 'A new zone reports with severity 10' },
    { type: 'urgency_changed', text: 'Zone B time-criticality rises from 5 to 8' },
    { type: 'request_updated', text: 'Zone C doubles its shelter request' },
  ];
  return (
    <div className="fp-events">
      <p className="fp-note">Example events of the kind the simulator accepts (illustrative).</p>
      <ol>
        {events.map((e) => (
          <li key={e.type}>
            <code>{e.type}</code>
            <span>{e.text}</span>
          </li>
        ))}
      </ol>
      <p className="fp-callout">
        Each event creates a new snapshot. Urgency is rescored, every policy re-runs, and the engine
        states what changed, including when the plan stays the same.
      </p>
    </div>
  );
}

function ExplanationPanel() {
  const medical = demoResources.find((r) => r.id === 'medical_kits') ?? demoResources[0];
  return (
    <div className="fp-explain">
      <p className="fp-callout">
        {medical.label}: {formatInt(medical.requested)} requested, {formatInt(medical.stock)} in
        stock. At least <strong className="num">{formatInt(medical.shortfall)}</strong> stay unmet
        under any policy. The question is only which zones carry the gap.
      </p>
      <p className="fp-note">
        Every allocated cell carries one of these reasons, taken from the computation itself:
      </p>
      <ul className="fp-limits">
        <li>
          <StatusBadge tone="ok">Met</StatusBadge> The request was filled in full.
        </li>
        <li>
          <StatusBadge tone="warn">Stock exhausted</StatusBadge> The resource's stock went to other
          zones: earlier arrivals under FCFS, more urgent zones under greedy and AidOS.
        </li>
        <li>
          <StatusBadge tone="warn">Exceeds stock</StatusBadge> The request is larger than the
          depot’s whole supply.
        </li>
        <li>
          <StatusBadge tone="critical">Depot empty</StatusBadge> No units of this resource exist.
        </li>
      </ul>
    </div>
  );
}

function ComparisonPanel() {
  const rows = [
    { policy: 'First come, first served', note: 'Baseline · built', tone: 'built' as const },
    { policy: 'Urgency greedy', note: 'Baseline · built', tone: 'built' as const },
    { policy: 'AidOS', note: 'Fuzzy + CP-SAT · built', tone: 'built' as const },
    { policy: 'AidOS balanced', note: 'Coverage floor · built', tone: 'built' as const },
  ];
  const metrics = [
    'Unit coverage',
    'Urgency-weighted coverage',
    'Fairness (Jain)',
    'Unmet high-urgency',
  ];
  return (
    <div className="fp-compare">
      <div className="fp-matrix__scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Policy</th>
              {metrics.map((m) => (
                <th key={m} scope="col">
                  {m}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.policy}>
                <th scope="row">
                  {row.policy}
                  <StatusBadge tone={row.tone}>{row.note}</StatusBadge>
                </th>
                {metrics.map((m) => (
                  <td key={m} className="fp-compare__empty">
                    <span aria-label="Averages are on the dashboard's Evaluation page">—</span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="fp-note">
        One-scenario comparisons run live in the dashboard. Comparisons of all four policies over
        many synthetic scenarios are on the dashboard&apos;s Evaluation page, including the metrics
        where a baseline ties with or beats AidOS. They describe the simulation, not real outcomes.
      </p>
    </div>
  );
}

function OversightPanel() {
  const steps = [
    { label: 'Candidate plan', body: 'Computed on a copy of the snapshot. Nothing is consumed.' },
    { label: 'Coordinator review', body: 'Inspect allocations, shortfalls and reasons.' },
    {
      label: 'Committed',
      body: 'Stock is dispatched exactly once, tied to the snapshot it was planned on.',
    },
  ];
  return (
    <div className="fp-oversight">
      <ol>
        {steps.map((s, i) => (
          <li key={s.label}>
            <span className="fp-oversight__index num" aria-hidden="true">
              {i + 1}
            </span>
            <div>
              <p className="fp-oversight__label">{s.label}</p>
              <p>{s.body}</p>
            </div>
          </li>
        ))}
      </ol>
      <p className="fp-note">AidOS is decision support. It never controls a real operation.</p>
    </div>
  );
}
