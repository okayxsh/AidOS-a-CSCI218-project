import type { ReactNode } from 'react';

export type BadgeTone =
  'built' | 'partial' | 'planned' | 'synthetic' | 'warn' | 'critical' | 'ok' | 'neutral';

interface StatusBadgeProps {
  tone: BadgeTone;
  children: ReactNode;
  dot?: boolean;
  title?: string;
}

/** Small status label. The text always states the status; colour only reinforces it. */
export function StatusBadge({ tone, children, dot = false, title }: StatusBadgeProps) {
  return (
    <span className={`badge${tone === 'neutral' ? '' : ` badge--${tone}`}`} title={title}>
      {dot && <span className="badge__dot" aria-hidden="true" />}
      {children}
    </span>
  );
}

export function SyntheticBadge() {
  return (
    <StatusBadge
      tone="synthetic"
      dot
      title="All scenarios are synthetic. No real disaster, medical or humanitarian data."
    >
      Synthetic data
    </StatusBadge>
  );
}
