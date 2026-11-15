import { demoResources, demoScenarioId, demoTotals } from '../content/demoScenario';
import { formatInt, resourceColour } from '../lib/format';

const NAV = [
  { label: 'Overview', active: true },
  { label: 'Scenarios' },
  { label: 'Inventory' },
  { label: 'Allocation' },
  { label: 'Simulation' },
  { label: 'Evaluation' },
];

/**
 * A static picture of the dashboard's overview for the landing hero, built from the
 * synthetic demo fixture's inputs. It shows no allocation results.
 */
export function DashboardPreview() {
  const summary = `Preview of the AidOS dashboard for the synthetic scenario ${demoScenarioId}: ${demoTotals.zones} zones request ${demoTotals.requested} units against ${demoTotals.stock} in stock, a shortfall of ${demoTotals.shortfall} units.`;

  return (
    <figure className="preview">
      <figcaption className="visually-hidden">{summary}</figcaption>
      <div className="preview__window dash-palette" aria-hidden="true">
        <div className="preview__bar">
          <span className="preview__dots">
            <i />
            <i />
            <i />
          </span>
          <span className="preview__crumb">
            Overview <span className="mono">/ {demoScenarioId}</span>
          </span>
          <span className="preview__tag">Preview · synthetic scenario</span>
        </div>
        <div className="preview__body">
          <nav className="preview__side">
            {NAV.map((item) => (
              <span key={item.label} className={item.active ? 'is-active' : undefined}>
                {item.label}
              </span>
            ))}
          </nav>
          <div className="preview__main">
            <div className="preview__kpis">
              <div>
                <span>Active zones</span>
                <b className="num">{demoTotals.zones}</b>
              </div>
              <div>
                <span>Units in stock</span>
                <b className="num">{formatInt(demoTotals.stock)}</b>
              </div>
              <div>
                <span>Units requested</span>
                <b className="num">{formatInt(demoTotals.requested)}</b>
              </div>
              <div className="is-warn">
                <span>Shortfall</span>
                <b className="num">{formatInt(demoTotals.shortfall)}</b>
              </div>
            </div>
            <div className="preview__resources">
              {demoResources.map((r, i) => (
                <div key={r.id} className="preview__res">
                  <div className="preview__res-head">
                    <span>
                      <i style={{ background: resourceColour(r.id, i) }} />
                      {r.label}
                    </span>
                    {r.shortfall > 0 && (
                      <small className="num">{formatInt(r.shortfall)} short</small>
                    )}
                  </div>
                  <div className="preview__track">
                    <i
                      style={{
                        width: `${Math.min(100, (r.stock / Math.max(r.requested, 1)) * 100)}%`,
                      }}
                    />
                  </div>
                  <p className="num">
                    {formatInt(r.stock)} in stock · {formatInt(r.requested)} requested
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </figure>
  );
}
