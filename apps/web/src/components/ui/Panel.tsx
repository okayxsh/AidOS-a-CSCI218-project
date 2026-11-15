import type { ReactNode } from 'react';

interface PanelProps {
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  /** Heading level inside the page outline. */
  level?: 2 | 3;
}

/** A titled dashboard region. Panels are never nested inside other panels. */
export function Panel({ title, description, actions, children, className, level = 2 }: PanelProps) {
  const Heading = level === 2 ? 'h2' : 'h3';
  return (
    <section className={['panel', className].filter(Boolean).join(' ')}>
      <header className="panel__head">
        <div>
          <Heading className="panel__title">{title}</Heading>
          {description && <p className="panel__desc">{description}</p>}
        </div>
        {actions && <div className="panel__actions">{actions}</div>}
      </header>
      {children}
    </section>
  );
}
