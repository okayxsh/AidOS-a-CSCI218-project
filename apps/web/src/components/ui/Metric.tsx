import { useEffect, type ReactNode } from 'react';

/** Last value seen per metric label, so a scenario switch can mark what changed. */
const lastSeen = new Map<string, string>();

interface MetricProps {
  label: string;
  value: ReactNode;
  unit?: string;
  detail?: ReactNode;
  tone?: 'default' | 'warn' | 'ok' | 'critical';
}

/** One summary figure. The value is always a backend-provided number or state. */
export function Metric({ label, value, unit, detail, tone = 'default' }: MetricProps) {
  const shown = typeof value === 'string' || typeof value === 'number' ? String(value) : null;
  const previous = shown === null ? undefined : lastSeen.get(label);
  const changed = previous !== undefined && previous !== shown;
  useEffect(() => {
    if (shown !== null) lastSeen.set(label, shown);
  }, [label, shown]);

  return (
    <div className={`metric metric--${tone}`}>
      <dt className="metric__label">{label}</dt>
      <dd
        className={`metric__value${typeof value === 'string' && /[a-z]/i.test(value) ? ' metric__value--text' : ''}${changed ? ' is-changed' : ''}`}
      >
        <span className="num">{value}</span>
        {unit && <span className="metric__unit">{unit}</span>}
      </dd>
      {detail && <dd className="metric__detail">{detail}</dd>}
    </div>
  );
}
