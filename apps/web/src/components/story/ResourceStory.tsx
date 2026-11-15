import { useGSAP } from '@gsap/react';
import { Component, lazy, Suspense, useEffect, useRef, useState, type ReactNode } from 'react';
import { demoResources, demoTotals, demoZones } from '../../content/demoScenario';
import { ADAPT_EXAMPLE, CHAPTERS, type ChapterStatus } from '../../content/story';
import { formatInt, formatRating, zoneShortName } from '../../lib/format';
import { hasWebGL, prefersReducedMotion, ScrollTrigger } from '../../lib/motion';
import { useMediaQuery } from '../../lib/useMediaQuery';
import { RequestBar } from '../RequestBar';
import { SectionHeading } from '../ui/SectionHeading';
import { StatusBadge, type BadgeTone } from '../ui/StatusBadge';
import { NetworkPoster } from './NetworkPoster';
import type { StoryConductor } from './NetworkScene';

const NetworkScene = lazy(() => import('./NetworkScene'));

const STATUS_TONE: Record<ChapterStatus, BadgeTone> = {
  scenario: 'synthetic',
  built: 'built',
  concept: 'planned',
  partial: 'partial',
  illustrated: 'planned',
};
const STATUS_WORD: Record<ChapterStatus, string> = {
  scenario: 'Synthetic data',
  built: 'Built',
  concept: 'Concept',
  partial: 'Partly built',
  illustrated: 'Illustration',
};

/** If the 3D chunk or WebGL fails, the poster stays: the story never depends on the canvas. */
class SceneBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

const medical = demoResources.find((r) => r.id === ADAPT_EXAMPLE.resourceId);

function labelFor(key: string, active: number): string {
  if (key === 'depot') {
    if (active === 8 && medical)
      return `Depot · medical ${medical.stock} → ${medical.stock - ADAPT_EXAMPLE.lostUnits} (example)`;
    if (active >= 4 && active !== 5)
      return `Depot · ${formatInt(demoTotals.stock)} in stock · ${formatInt(demoTotals.requested)} requested`;
    return `Depot · ${formatInt(demoTotals.stock)} units in stock`;
  }
  if (key === 'zone-d') return 'Zone D · example event';
  const z = demoZones.find((zone) => zone.id === key);
  if (!z) return key;
  const name = zoneShortName(z.name);
  if (active === 5)
    return `${name} · S ${formatRating(z.severity)} · V ${formatRating(z.vulnerability)} · T ${formatRating(z.timeCriticality)}`;
  if (active >= 3) {
    const total = Object.values(z.demand).reduce((a, b) => a + b, 0);
    return `${name} · ${formatInt(total)} requested`;
  }
  return `${name} · severity ${formatRating(z.severity)}`;
}

/** Chapter-specific evidence rendered as real HTML beside the 3D visual. */
function ChapterDetail({ id }: { id: string }) {
  if (id === 'shortage') {
    return (
      <ul className="story__bars">
        {demoResources.map((r) => (
          <li key={r.id}>
            <p className="story__bar-label">
              <span>{r.label}</span>
              <span className="story__short num">
                {r.shortfall > 0 ? `${formatInt(r.shortfall)} short` : 'Covered'}
              </span>
            </p>
            <RequestBar
              label={r.label}
              stock={r.stock}
              requested={r.requested}
              segments={r.byZone.map((e) => {
                const zone = demoZones.find((z) => z.id === e.zoneId);
                return {
                  key: e.zoneId,
                  label: zone ? zoneShortName(zone.name) : e.zoneId,
                  units: e.units,
                };
              })}
            />
          </li>
        ))}
      </ul>
    );
  }
  if (id === 'fuzzy') {
    return (
      <table className="story__ratings">
        <caption className="visually-hidden">Fuzzy logic inputs per zone, rated 0 to 10</caption>
        <thead>
          <tr>
            <th scope="col">Zone</th>
            <th scope="col">Severity</th>
            <th scope="col">Vulnerability</th>
            <th scope="col">Time-criticality</th>
            <th scope="col">Urgency</th>
          </tr>
        </thead>
        <tbody>
          {demoZones.map((z) => (
            <tr key={z.id}>
              <th scope="row">{zoneShortName(z.name)}</th>
              <td className="num">{formatRating(z.severity)}</td>
              <td className="num">{formatRating(z.vulnerability)}</td>
              <td className="num">{formatRating(z.timeCriticality)}</td>
              <td className="story__pending">In the dashboard</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  if (id === 'constraints') {
    return (
      <ul className="story__rules mono">
        <li>0 ≤ allocated ≤ requested</li>
        <li>Σ allocated ≤ stock, per resource</li>
        <li>whole units only</li>
      </ul>
    );
  }
  return null;
}

export function ResourceStory() {
  const sectionRef = useRef<HTMLElement>(null);
  const stepsRef = useRef<HTMLOListElement>(null);
  const conductor = useRef<StoryConductor>({ target: 0, cardRight: 0, panelTop: Infinity });
  const stageRef = useRef<HTMLDivElement>(null);
  const labels = useRef(new Map<string, HTMLElement>());
  const [active, setActive] = useState(0);
  // Without IntersectionObserver there is nothing to wait for: load as soon as WebGL exists.
  const [load3D, setLoad3D] = useState(() => !('IntersectionObserver' in window) && hasWebGL());
  const [failed, setFailed] = useState(false);
  const compact = useMediaQuery('(max-width: 900px)');
  const reduced = useMediaQuery('(prefers-reduced-motion: reduce)');

  // Fetch the 3D chunk only when the story approaches and WebGL exists.
  useEffect(() => {
    const el = sectionRef.current;
    if (!el || !hasWebGL() || !('IntersectionObserver' in window)) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setLoad3D(true);
          io.disconnect();
        }
      },
      { rootMargin: '900px 0px' },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  // Native scroll is the source of truth; GSAP only measures it.
  useGSAP(
    () => {
      const steps = stepsRef.current;
      if (!steps) return;
      const items = Array.from(steps.querySelectorAll<HTMLElement>('.story__step'));
      const last = CHAPTERS.length - 1;
      const update = (self: ScrollTrigger) => {
        const stepHeight = items[0]?.offsetHeight || window.innerHeight;
        const c = Math.min(last, Math.max(0, (self.scroll() - self.start) / stepHeight));
        conductor.current.target = c;
        conductor.current.invalidate?.();
        const index = Math.round(c);
        setActive((prev) => (prev === index ? prev : index));
        // Phones stack the panel over the scene: labels must stay above its live top edge.
        const stage = stageRef.current;
        const panel = items[index]?.querySelector<HTMLElement>('.story__panel');
        conductor.current.panelTop =
          stage && panel && window.matchMedia?.('(max-width: 900px)').matches
            ? panel.getBoundingClientRect().top - stage.getBoundingClientRect().top
            : Infinity;
        if (!prefersReducedMotion()) {
          items.forEach((item, i) => {
            const distance = Math.min(1, Math.abs(c - i) * 1.4);
            item.style.setProperty('--focus', String(1 - distance));
          });
        }
      };
      // Labels must not slide under the reading card: record its right edge on wide screens.
      const measureCard = () => {
        const panel = steps.querySelector<HTMLElement>('.story__panel');
        const stage = stageRef.current;
        const stacked = window.matchMedia?.('(max-width: 900px)').matches;
        conductor.current.cardRight =
          panel && stage && !stacked
            ? panel.getBoundingClientRect().right - stage.getBoundingClientRect().left + 16
            : 0;
      };
      const trigger = ScrollTrigger.create({
        trigger: steps,
        start: 'top top',
        end: 'bottom bottom',
        onUpdate: update,
        onRefresh: (self) => {
          measureCard();
          update(self);
        },
      });
      document.fonts?.ready.then(() => ScrollTrigger.refresh());
      return () => trigger.kill();
    },
    { scope: sectionRef },
  );

  const poster = <NetworkPoster />;
  const show3D = load3D && !failed;
  const labelKeys = ['depot', ...demoZones.map((z) => z.id), 'zone-d'];

  return (
    <section className="story" ref={sectionRef} aria-labelledby="story-title">
      <div className="container story__intro">
        <SectionHeading
          id="story-title"
          title={
            <>
              How a shortage becomes <em>a decision.</em>
            </>
          }
          lede="One synthetic scenario, followed from the depot to the coordinator. Scroll to move through it; every number below comes from the scenario file the engine serves."
        />
      </div>

      <div className="story__body">
        <div className="story__stage" ref={stageRef}>
          <div className="story__aurora" aria-hidden="true" />
          {show3D ? (
            <SceneBoundary fallback={poster}>
              <Suspense fallback={poster}>
                <NetworkScene
                  conductor={conductor}
                  labels={labels}
                  reduced={reduced}
                  compact={compact}
                  onLost={() => setFailed(true)}
                />
              </Suspense>
            </SceneBoundary>
          ) : (
            poster
          )}
          {show3D && (
            <div className="story__labels" aria-hidden="true">
              {labelKeys.map((key) => (
                <span
                  key={key}
                  className={`story__label${key === 'depot' ? ' story__label--depot' : ''}`}
                  ref={(el) => {
                    if (el) labels.current.set(key, el);
                    else labels.current.delete(key);
                  }}
                >
                  {labelFor(key, active)}
                </span>
              ))}
            </div>
          )}
        </div>

        <ol className="story__steps" ref={stepsRef}>
          {CHAPTERS.map((chapter, i) => (
            <li
              key={chapter.id}
              className={`story__step${i === active ? ' is-active' : ''}`}
              aria-current={i === active ? 'step' : undefined}
            >
              <div className="story__panel">
                <h3 className="story__title">{chapter.title}</h3>
                {chapter.status && (
                  <p className="story__status">
                    <StatusBadge tone={STATUS_TONE[chapter.status.tone]}>
                      {STATUS_WORD[chapter.status.tone]}
                    </StatusBadge>
                    <span>{chapter.status.text}</span>
                  </p>
                )}
                <p className="story__text">{chapter.body}</p>
                <ChapterDetail id={chapter.id} />
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
