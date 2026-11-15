import { STATUS_LABEL, WORKFLOW } from '../content/landing';
import { SectionHeading } from './ui/SectionHeading';
import { StatusBadge } from './ui/StatusBadge';

export function HowItWorks() {
  return (
    <section id="how-it-works" className="section workflow" aria-labelledby="how-title">
      <div className="container">
        <SectionHeading
          id="how-title"
          title="How AidOS works"
          lede="Five steps from scenario to decision. Each one is labelled with what exists in the build today and what is still planned."
        />
        <ol className="workflow__steps">
          {WORKFLOW.map((step, index) => (
            <li key={step.title} className={`workflow__step workflow__step--${step.status}`}>
              <span className="workflow__node num" aria-hidden="true">
                {index + 1}
              </span>
              <h3>{step.title}</h3>
              <p className="workflow__technique">{step.technique}</p>
              <p className="workflow__body">{step.body}</p>
              <p className="workflow__status">
                <StatusBadge tone={step.status}>{STATUS_LABEL[step.status]}</StatusBadge>
                <span>{step.statusNote}</span>
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
