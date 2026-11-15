import { SEGMENT_SHADES } from '../lib/display';
import { formatInt } from '../lib/format';

interface RequestBarProps {
  label: string;
  segments: { key: string; label: string; units: number }[];
  stock: number;
  requested: number;
}

/**
 * Requests stacked by zone, with the depot's stock marked on the same scale.
 * Everything to the right of the marker cannot be served by any policy.
 */
export function RequestBar({ label, segments, stock, requested }: RequestBarProps) {
  const markerAt = requested === 0 ? 100 : Math.min(100, (stock / requested) * 100);
  return (
    <div
      className="request-bar"
      role="img"
      aria-label={`${label}: ${formatInt(requested)} requested across ${segments.length} zones, ${formatInt(stock)} in stock`}
    >
      {requested === 0 ? (
        <span className="request-bar__empty">No requests</span>
      ) : (
        segments
          .filter((s) => s.units > 0)
          .map((s, i) => (
            <span
              key={s.key}
              className="request-bar__seg"
              style={{ flexGrow: s.units, background: SEGMENT_SHADES[i % SEGMENT_SHADES.length] }}
              title={`${s.label}: ${formatInt(s.units)}`}
            >
              <span className="request-bar__zone">{s.label.replace(/^Zone\s+/i, '')}</span>
              <span className="num">{formatInt(s.units)}</span>
            </span>
          ))
      )}
      {requested > stock && (
        // Requests past the stock line: the part no plan can serve.
        <span className="request-bar__over" style={{ left: `${markerAt}%` }} aria-hidden="true" />
      )}
      <span
        className={[
          'request-bar__stock',
          markerAt > 82 && 'request-bar__stock--end',
          markerAt < 18 && 'request-bar__stock--start',
        ]
          .filter(Boolean)
          .join(' ')}
        style={{ left: `${markerAt}%` }}
      >
        <span className="num">{formatInt(stock)} in stock</span>
      </span>
    </div>
  );
}
