import { ArrowDown } from 'lucide-react';
import { LaunchDashboardButton } from './ui/Button';

export function LandingHero() {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <h1 id="hero-title" className="hero__title">
        <span>When every resource matters,</span> <em>every decision counts.</em>
      </h1>
      <p className="hero__sub">
        AidOS is an explainable AI simulation for allocating limited humanitarian supplies between
        competing crisis zones as conditions change.
      </p>
      <div className="hero__actions">
        <LaunchDashboardButton />
        <a className="btn btn--secondary" href="#how-it-works">
          Explore how it works
          <ArrowDown size={16} aria-hidden="true" />
        </a>
      </div>
      <p className="hero__note">
        <span className="hero__note-dot" aria-hidden="true" />
        CSCI218 student prototype · synthetic scenarios only · not a real dispatch system
      </p>
    </section>
  );
}
