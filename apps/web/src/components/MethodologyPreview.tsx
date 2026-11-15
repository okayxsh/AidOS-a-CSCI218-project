import fuzzyConfig from '../../../api/aidos/config/fuzzy_rules.json';
import { SectionHeading } from './ui/SectionHeading';
import { StatusBadge } from './ui/StatusBadge';

/*
 * The engine's own versioned membership functions (apps/api/aidos/config/fuzzy_rules.json),
 * read at build time so this chart can never drift from the scoring code. Drawing a curve
 * is not scoring: the landing page still computes no urgency score.
 */
type Shape = [number, number, number, number]; // trapezoid a ≤ b ≤ c ≤ d
const toTrapezoid = (points: number[]): Shape =>
  points.length === 3
    ? [points[0], points[1], points[1], points[2]]
    : [points[0], points[1], points[2], points[3]];
const COLOURS: Record<string, string> = {
  low: 'var(--blue)',
  medium: 'var(--teal)',
  high: 'var(--violet)',
};
const SETS = Object.entries(fuzzyConfig.inputs.severity.terms).map(([name, mf]) => ({
  name,
  shape: toTrapezoid(mf.points),
  colour: COLOURS[name] ?? 'var(--text-2)',
}));
const EXAMPLE_RULE = fuzzyConfig.rules.find((r) => r.id === 'R25') ?? fuzzyConfig.rules[0];
const EXAMPLE_INPUT = 7;

function membership([a, b, c, d]: Shape, x: number): number {
  if (x < a || x > d) return 0;
  if (x >= b && x <= c) return 1;
  if (x < b) return (x - a) / (b - a);
  return (d - x) / (d - c);
}

const W = 520;
const H = 210;
const PAD = { l: 36, r: 16, t: 34, b: 34 };
const sx = (x: number) => PAD.l + (x / 10) * (W - PAD.l - PAD.r);
const sy = (y: number) => H - PAD.b - y * (H - PAD.t - PAD.b);

function MembershipChart() {
  const memberships = SETS.map((s) => ({ ...s, mu: membership(s.shape, EXAMPLE_INPUT) }));
  const summary = memberships.map((m) => `${m.name} ${m.mu.toFixed(2)}`).join(', ');
  return (
    <figure className="tech__figure">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="membership"
        role="img"
        aria-label={`Membership functions low, medium and high over a 0 to 10 severity rating. At severity ${EXAMPLE_INPUT}: ${summary}.`}
      >
        {[0, 0.5, 1].map((y) => (
          <g key={y}>
            <line x1={PAD.l} x2={W - PAD.r} y1={sy(y)} y2={sy(y)} className="membership__grid" />
            <text x={PAD.l - 10} y={sy(y) + 4} textAnchor="end" className="membership__tick">
              {y}
            </text>
          </g>
        ))}
        {[0, 2, 4, 6, 8, 10].map((x) => (
          <text key={x} x={sx(x)} y={H - 12} textAnchor="middle" className="membership__tick">
            {x}
          </text>
        ))}
        {SETS.map(({ name, shape: [a, b, c, d], colour }) => (
          <g key={name}>
            <polyline
              points={`${sx(a)},${sy(0)} ${sx(b)},${sy(1)} ${sx(c)},${sy(1)} ${sx(d)},${sy(0)}`}
              fill="none"
              stroke={colour}
              strokeWidth="2"
              strokeLinejoin="round"
            />
            <text
              x={sx((b + c) / 2)}
              y={sy(1) - 7}
              textAnchor="middle"
              className="membership__label"
              fill={colour}
            >
              {name}
            </text>
          </g>
        ))}
        <line
          x1={sx(EXAMPLE_INPUT)}
          x2={sx(EXAMPLE_INPUT)}
          y1={sy(0)}
          y2={sy(1)}
          className="membership__probe"
        />
        {memberships
          .filter((m) => m.mu > 0)
          .map((m) => (
            <g key={m.name}>
              <circle cx={sx(EXAMPLE_INPUT)} cy={sy(m.mu)} r="4" fill={m.colour} />
              <text
                x={sx(EXAMPLE_INPUT) - 10}
                y={sy(m.mu) + 4}
                textAnchor="end"
                className="membership__value"
              >
                μ {m.name} = {m.mu.toFixed(2)}
              </text>
            </g>
          ))}
      </svg>
      <figcaption>
        Severity rated 7: partly “medium”, mostly “high”. The engine’s own sets (rules v
        {fuzzyConfig.version}).
      </figcaption>
    </figure>
  );
}

const STATES = ['READY', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ERROR'];

export function MethodologyPreview() {
  return (
    <section id="technology" className="section tech" aria-labelledby="tech-title">
      <div className="container">
        <SectionHeading
          id="tech-title"
          title={
            <>
              Three explainable techniques, <em>no black box.</em>
            </>
          }
          lede="AidOS is built from classical AI methods whose every step can be inspected and tested. No machine-learning model and no language model makes the decisions."
        />

        <div className="tech__rows">
          <article className="tech__row" aria-labelledby="tech-fuzzy">
            <div className="tech__copy">
              <h3 id="tech-fuzzy">Fuzzy logic</h3>
              <p>
                Field reports are imprecise. Fuzzy sets let “fairly severe” count as partly medium
                and partly high. Then 27 rules turn three ratings into one urgency score from 0 to
                100, and every rule’s contribution to that score can be read back.
              </p>
              <pre className="tech__code">
                <code>
                  {EXAMPLE_RULE.id}: IF severity is {EXAMPLE_RULE.if.severity}
                  {'\n'}
                  {'   '}AND time_criticality is {EXAMPLE_RULE.if.time_criticality}
                  {'\n'}
                  {'   '}AND vulnerability is {EXAMPLE_RULE.if.vulnerability}
                  {'\n'}
                  {'   '}THEN urgency is {EXAMPLE_RULE.then}
                </code>
              </pre>
              <p className="tech__meta">
                <StatusBadge tone="built">Built</StatusBadge>
                Stage 2 · zero-order Sugeno: product AND, weighted average of rule outputs; sets and
                rules in a versioned config
              </p>
            </div>
            <MembershipChart />
          </article>

          <article className="tech__row" aria-labelledby="tech-csp">
            <div className="tech__copy">
              <h3 id="tech-csp">Constraint satisfaction</h3>
              <p>
                Allocation is an integer program. Hard limits are never traded away for a higher
                score: if a plan breaks one, it is not a plan. OR-Tools CP-SAT searches the feasible
                set and reports its status truthfully.
              </p>
              <p className="tech__meta">
                <StatusBadge tone="built">Built</StatusBadge>
                Stage 2 · OR-Tools CP-SAT, solved lexicographically; FCFS and urgency greedy on the
                same limits
              </p>
            </div>
            <figure className="tech__figure tech__formula">
              <dl>
                <div>
                  <dt>maximise</dt>
                  <dd className="mono">
                    Σ<sub>z,r</sub> w<sub>r</sub> · (ε + u<sub>z</sub>) · x<sub>z,r</sub>
                  </dd>
                </div>
                <div>
                  <dt>subject to</dt>
                  <dd className="mono">
                    0 ≤ x<sub>z,r</sub> ≤ d<sub>z,r</sub>
                  </dd>
                </div>
                <div>
                  <dt />
                  <dd className="mono">
                    Σ<sub>z</sub> x<sub>z,r</sub> ≤ S<sub>r</sub>
                  </dd>
                </div>
                <div>
                  <dt />
                  <dd className="mono">
                    x<sub>z,r</sub> ∈ ℤ
                  </dd>
                </div>
              </dl>
              <figcaption>
                x allocated units · d requested · S depot stock · u fuzzy urgency · w resource
                weight
              </figcaption>
            </figure>
          </article>

          <article className="tech__row" aria-labelledby="tech-fsm">
            <div className="tech__copy">
              <h3 id="tech-fsm">Finite state machine</h3>
              <p>
                A simulation session moves through explicit, tested states. Events are applied
                atomically to a copy of the snapshot; computing a plan never touches stock. Only a
                dispatch does, exactly once, against the snapshot it was planned on.
              </p>
              <p className="tech__meta">
                <StatusBadge tone="built">Built</StatusBadge>
                Stage 3 · events: zone added, urgency changed, supply arrived or lost, request
                updated, zone resolved, clock advanced, plan dispatched
              </p>
            </div>
            <figure className="tech__figure">
              <ol className="fsm" aria-label="Simulation states in order">
                {STATES.map((s) => (
                  <li key={s} className="fsm__state mono">
                    {s}
                  </li>
                ))}
              </ol>
              <figcaption>
                Events are accepted only while ACTIVE. Pause freezes the session; reset returns to
                READY from any state; ERROR is entered only if an engine check fails.
              </figcaption>
            </figure>
          </article>
        </div>

        <p className="tech__baselines">
          Every method is measured against two simple baselines, first come first served and urgency
          greedy, on the same scenarios and the same metrics. A tie with a baseline is a result we
          report, not one we hide.
        </p>
      </div>
    </section>
  );
}
