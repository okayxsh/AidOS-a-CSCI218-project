import { ArrowUpRight } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router';

type Variant = 'primary' | 'secondary' | 'quiet' | 'accent';

interface LinkButtonProps {
  to: string;
  variant?: Variant;
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

/** A router link styled as a button. Primary buttons carry the arrow disc. */
export function LinkButton({
  to,
  variant = 'primary',
  children,
  className,
  onClick,
}: LinkButtonProps) {
  return (
    <Link
      to={to}
      className={['btn', `btn--${variant}`, className].filter(Boolean).join(' ')}
      onClick={onClick}
    >
      {children}
      {variant === 'primary' && (
        <span className="btn__icon" aria-hidden="true">
          <ArrowUpRight size={16} strokeWidth={2} />
        </span>
      )}
    </Link>
  );
}

/** The one call to action used everywhere on the landing page. */
export function LaunchDashboardButton({
  className,
  onClick,
}: {
  className?: string;
  onClick?: () => void;
}) {
  return (
    <LinkButton to="/dashboard" className={className} onClick={onClick}>
      Launch Dashboard
    </LinkButton>
  );
}
