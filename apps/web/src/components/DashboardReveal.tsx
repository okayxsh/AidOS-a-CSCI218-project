import { DashboardPreview } from './DashboardPreview';
import { LaunchDashboardButton } from './ui/Button';

/**
 * The story's last scene: the same dashboard preview the hero opened with, now brought
 * square to the viewer, with the action that leads into the working system.
 */
export function DashboardReveal() {
  return (
    <section className="reveal" aria-labelledby="reveal-title">
      <div className="reveal__frame">
        <div className="reveal__aurora" aria-hidden="true" />
        <div className="reveal__copy">
          <h2 id="reveal-title">
            From the story <em>to the system.</em>
          </h2>
          <p>
            The dashboard loads this same synthetic scenario from the engine. Run the FCFS baseline,
            inspect every allocation and the limit behind it, then switch scenarios.
          </p>
          <LaunchDashboardButton />
        </div>
        <div className="reveal__stage">
          <DashboardPreview />
        </div>
      </div>
    </section>
  );
}
