import { Link } from 'react-router';
import { Logo } from '../components/ui/Logo';

/** Shown for unknown dashboard routes (inside the shell) and unknown top-level routes. */
export function DashboardNotFound() {
  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1 className="page-head__title">This dashboard page does not exist</h1>
          <p className="page-head__desc">
            Use the navigation, or go back to the <Link to="/dashboard">overview</Link>.
          </p>
        </div>
      </header>
    </div>
  );
}

export default function NotFound() {
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
