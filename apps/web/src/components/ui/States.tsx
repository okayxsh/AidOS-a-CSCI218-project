import { CircleAlert, Inbox, RotateCcw, ServerOff } from 'lucide-react';
import type { ReactNode } from 'react';
import { ApiError } from '../../api/client';

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="state state--loading" role="status" aria-live="polite">
      <span className="visually-hidden">{label}…</span>
      <div className="skeleton skeleton--title" />
      <div className="skeleton-row">
        <div className="skeleton" />
        <div className="skeleton" />
        <div className="skeleton" />
        <div className="skeleton" />
      </div>
      <div className="skeleton skeleton--block" />
    </div>
  );
}

interface ErrorStateProps {
  error: Error | undefined;
  onRetry?: () => void;
  title?: string;
}

export function ErrorState({ error, onRetry, title }: ErrorStateProps) {
  const offline = error instanceof ApiError && error.kind === 'network';
  const Icon = offline ? ServerOff : CircleAlert;
  return (
    <div className="state state--error" role="alert">
      <Icon size={22} aria-hidden="true" />
      <div>
        <h2 className="state__title">
          {title ?? (offline ? 'The AidOS engine is not running' : 'Something went wrong')}
        </h2>
        <p className="state__body">{error?.message ?? 'Unknown error.'}</p>
        {offline && (
          <p className="state__help">
            Start it from <code>apps/api</code> with{' '}
            <code>uv run uvicorn aidos.main:app --port 8000</code>, then retry. The dashboard never
            shows numbers the engine did not compute.
          </p>
        )}
        {onRetry && (
          <button type="button" className="btn btn--quiet state__retry" onClick={onRetry}>
            <RotateCcw size={15} aria-hidden="true" />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  children,
  action,
}: {
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="state state--empty">
      <Inbox size={22} aria-hidden="true" />
      <div>
        <h2 className="state__title">{title}</h2>
        {children && <div className="state__body">{children}</div>}
        {action && <div className="state__action">{action}</div>}
      </div>
    </div>
  );
}
