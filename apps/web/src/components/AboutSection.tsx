import { Database, FlaskConical, Hand, ShieldAlert } from 'lucide-react';
import { SectionHeading } from './ui/SectionHeading';

const SCOPE = [
  {
    icon: Database,
    title: 'Synthetic data only',
    body: 'Every scenario is invented for the simulator and declares itself synthetic. No real disaster, medical or personal records.',
  },
  {
    icon: Hand,
    title: 'People decide',
    body: 'AidOS suggests and explains. Committing a plan is always a human action.',
  },
  {
    icon: ShieldAlert,
    title: 'Not an operational system',
    body: 'It is not a dispatch, medical or humanitarian service, and it is not deployed anywhere.',
  },
  {
    icon: FlaskConical,
    title: 'Claims follow evidence',
    body: 'Results come only from repeatable, seeded experiments on synthetic scenarios, and they include the cases where a baseline wins or ties.',
  },
];

export function AboutSection() {
  return (
    <section id="about" className="section about" aria-labelledby="about-title">
      <div className="container about__grid">
        <div>
          <SectionHeading
            id="about-title"
            title="A CSCI218 student project"
            lede="AidOS is a group project for CSCI218 Foundations of Artificial Intelligence at the University of Wollongong in Dubai, Autumn 2026. It answers the course's Project C brief: an emergency resource allocation simulation with explanations and measurable trade-offs."
          />
        </div>
        <ul className="about__scope">
          {SCOPE.map(({ icon: Icon, title, body }) => (
            <li key={title}>
              <Icon size={20} strokeWidth={1.75} aria-hidden="true" />
              <div>
                <h3>{title}</h3>
                <p>{body}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
