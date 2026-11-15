import { demoResources, demoTotals, demoZones } from '../../content/demoScenario';
import { formatInt, zoneShortName } from '../../lib/format';

/** Same authored layout as the 3D scene, seen from above (x, z). */
const POSITIONS: Record<string, [number, number]> = {
  'zone-a': [-5.2, -2.4],
  'zone-b': [4.9, -3.3],
  'zone-c': [2.7, 3.7],
};

/**
 * Static schematic of the resource network. Shown before the 3D chunk loads, and as the
 * permanent visual when WebGL is unavailable or the context is lost.
 */
export function NetworkPoster() {
  return (
    <svg
      className="story__poster"
      viewBox="-8 -6 16 12"
      role="img"
      aria-label={`Resource network: one depot with ${demoTotals.stock} units in stock, three zones requesting ${demoTotals.requested} units.`}
    >
      {[1, 2, 3, 4, 5, 6, 7].map((r) => (
        <circle key={r} r={r} fill="none" stroke="rgba(169,200,238,0.12)" strokeWidth="0.03" />
      ))}
      {demoZones.map((z) => {
        const [x, y] = POSITIONS[z.id] ?? [0, 0];
        return (
          <path
            key={`r-${z.id}`}
            d={`M0 0 Q ${x / 2} ${y / 2 - 1.4} ${x} ${y}`}
            fill="none"
            stroke="#7088a8"
            strokeWidth="0.05"
          />
        );
      })}
      <g>
        <polygon
          points="0,-1 0.87,-0.5 0.87,0.5 0,1 -0.87,0.5 -0.87,-0.5"
          fill="#0d1c30"
          stroke="#e8eef7"
          strokeWidth="0.05"
        />
        <text className="story__poster-label" y="-1.6" textAnchor="middle">
          Depot · {formatInt(demoTotals.stock)} in stock
        </text>
      </g>
      {demoZones.map((z) => {
        const [x, y] = POSITIONS[z.id] ?? [0, 0];
        const requested = demoResources.reduce((s, r) => s + (z.demand[r.id] ?? 0), 0);
        return (
          <g key={z.id} transform={`translate(${x} ${y})`}>
            <circle r="0.5" fill="#16304f" stroke="#e8eef7" strokeWidth="0.06" />
            <text className="story__poster-label" y={y > 0 ? 1.0 : -0.85} textAnchor="middle">
              {zoneShortName(z.name)} · {formatInt(requested)} requested
            </text>
          </g>
        );
      })}
    </svg>
  );
}
