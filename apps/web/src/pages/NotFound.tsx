import { useEffect } from 'react';
import { Link } from 'react-router';
import { useScenarioQuery } from '../state/scenario';
import { Logo } from '../components/ui/Logo';

/** Shown for unknown dashboard routes (inside the shell) and unknown top-level routes. */
export function DashboardNotFound() {
  const query = useScenarioQuery();
  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1 className="page-head__title">This dashboard page does not exist</h1>
          <p className="page-head__desc">
            Use the navigation, or go back to the <Link to={`/dashboard${query}`}>overview</Link>.
          </p>
        </div>
      </header>
    </div>
  );
}

export default function NotFound() {
  useEffect(() => {
    document.title = 'Page not found · AidOS';
  }, []);
  return (
    <main className="not-found">
      <Logo />
      <h1>Page not found</h1>
      <p>
        Go to the <Link to="/">AidOS home page</Link> or open the{' '}
        <Link to="/dashboard">dashboard</Link>.
      </p>
    </main>
  );
}
