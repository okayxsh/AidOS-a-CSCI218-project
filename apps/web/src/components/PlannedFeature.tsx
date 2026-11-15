import { Hammer } from 'lucide-react';
import type { ReactNode } from 'react';
import { StatusBadge } from './ui/StatusBadge';

interface PlannedFeatureProps {
  stage: number;
  title: string;
  summary: string;
  willShow: string[];
  dependsOn: string;
  children?: ReactNode;
}

/** States plainly that a page's engine work has not been built yet, and what it will contain. */
export function PlannedFeature({
  stage,
  title,
  summary,
  willShow,
  dependsOn,
  children,
}: PlannedFeatureProps) {
  return (
    <section className="planned" aria-labelledby="planned-title">
      <div className="planned__intro">
        <span className="planned__icon" aria-hidden="true">
          <Hammer size={20} />
        </span>
        <div>
          <div className="planned__head">
            <h2 id="planned-title">{title}</h2>
            <StatusBadge tone="planned">Planned · Stage {stage}</StatusBadge>
          </div>
          <p className="planned__summary">{summary}</p>
        </div>
      </div>
      <div className="planned__grid">
        <div>
          <h3>What this page will show</h3>
          <ul className="planned__list">
            {willShow.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3>What it depends on</h3>
          <p>{dependsOn}</p>
        </div>
      </div>
      {children}
    </section>
  );
}
