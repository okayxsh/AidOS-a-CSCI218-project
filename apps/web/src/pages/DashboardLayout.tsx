import {
  ArrowLeft,
  Boxes,
  ChartColumn,
  FolderOpen,
  GitBranch,
  LayoutDashboard,
  Menu,
  Scale,
  X,
  type LucideIcon,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router';
import { ScenarioSelector } from '../components/ScenarioSelector';
import { RouteErrorBoundary } from '../components/ui/RouteErrorBoundary';
import { Logo } from '../components/ui/Logo';
import { SyntheticBadge } from '../components/ui/StatusBadge';
import type { DashboardContext } from '../state/dashboard';
import {
  useActiveScenarioId,
  useHealth,
  useScenarioDetail,
  useScenarioQuery,
} from '../state/scenario';
import { forgetRequest } from '../state/useRequest';
import '../styles/dashboard.css';

/** How often the sidebar re-checks the engine, so "Engine online" cannot go stale. */
const HEALTH_RECHECK_MS = 20_000;

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
  plannedStage?: number;
}

const WORKSPACE: NavItem[] = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/dashboard/scenarios', label: 'Emergency scenarios', icon: FolderOpen },
  { to: '/dashboard/inventory', label: 'Resource inventory', icon: Boxes },
  { to: '/dashboard/allocate', label: 'Allocation results', icon: Scale },
  { to: '/dashboard/simulate', label: 'Simulation', icon: GitBranch },
  { to: '/dashboard/evaluate', label: 'Evaluation', icon: ChartColumn },
];

/** Pages for stages that are not built yet. Empty now: every dashboard page is built. */
const LATER: NavItem[] = [];

const TITLES: Record<string, string> = {
  '/dashboard': 'Overview',
  '/dashboard/scenarios': 'Emergency scenarios',
  '/dashboard/inventory': 'Resource inventory',
  '/dashboard/allocate': 'Allocation results',
  '/dashboard/simulate': 'Simulation',
  '/dashboard/evaluate': 'Evaluation',
};

function EngineStatus() {
  const health = useHealth();
  const retry = useRef(health.retry);
  useEffect(() => {
    retry.current = health.retry;
  });
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState !== 'visible') return;
      forgetRequest('health');
      retry.current();
    }, HEALTH_RECHECK_MS);
    return () => window.clearInterval(timer);
  }, []);
  if (health.status === 'loading') {
    return (
      <p className="engine-status">
        <span className="engine-status__dot is-pending" aria-hidden="true" /> Checking engine…
      </p>
    );
  }
  if (health.status === 'error' || !health.data) {
    return (
      <p className="engine-status is-offline">
        <span className="engine-status__dot" aria-hidden="true" /> Engine offline
        <button type="button" className="engine-status__retry" onClick={health.retry}>
          Retry
        </button>
      </p>
    );
  }
  return (
    <p className="engine-status is-online">
      <span className="engine-status__dot" aria-hidden="true" /> Engine online
      <span className="engine-status__meta mono">
        v{health.data.version} · stage {health.data.engine_stage}
      </span>
    </p>
  );
}

function SideNav({ onNavigate }: { onNavigate: () => void }) {
  const query = useScenarioQuery();
  const item = ({ to, label, icon: Icon, end, plannedStage }: NavItem) => (
    <li key={to}>
      <NavLink
        to={`${to}${query}`}
        end={end}
        onClick={onNavigate}
        className={({ isActive }) =>
          ['side-nav__link', isActive && 'is-active', plannedStage && 'is-planned']
            .filter(Boolean)
            .join(' ')
        }
      >
        <Icon size={18} strokeWidth={1.75} aria-hidden="true" />
        <span>{label}</span>
        {plannedStage && <span className="side-nav__stage">Stage {plannedStage}</span>}
      </NavLink>
    </li>
  );

  return (
    <nav className="side-nav" aria-label="Dashboard">
      <p className="side-nav__group" id="nav-workspace">
        Workspace
      </p>
      <ul aria-labelledby="nav-workspace">{WORKSPACE.map(item)}</ul>
      {LATER.length > 0 && (
        <>
          <p className="side-nav__group" id="nav-later">
            Later stages
          </p>
          <ul aria-labelledby="nav-later">{LATER.map(item)}</ul>
        </>
      )}
    </nav>
  );
}

/** Dashboard shell: sidebar, top bar with the scenario selector, and the active page. */
export default function DashboardLayout() {
  const [scenarioId] = useActiveScenarioId();
  const detail = useScenarioDetail(scenarioId);
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const wasOpen = useRef(false);
  const title = TITLES[location.pathname.replace(/\/$/, '')] ?? 'Not found';

  useEffect(() => {
    document.title = `${title} · AidOS dashboard`;
  }, [title]);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => event.key === 'Escape' && setMenuOpen(false);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [menuOpen]);

  // Phone drawer: move focus into it on open, and back to the menu button on close.
  useEffect(() => {
    if (menuOpen) closeButton.current?.focus();
    else if (wasOpen.current) menuButton.current?.focus();
    wasOpen.current = menuOpen;
  }, [menuOpen]);

  const context: DashboardContext = { scenarioId, detail };
  const close = () => setMenuOpen(false);

  return (
    <div className="dash dash-palette">
      <a className="skip-link" href="#dash-main" inert={menuOpen}>
        Skip to content
      </a>

      <aside className={`dash__side${menuOpen ? ' is-open' : ''}`} id="dash-sidebar">
        <div className="dash__brand">
          <Link to="/" aria-label="AidOS home" className="dash__brand-link">
            <Logo />
          </Link>
          <button
            type="button"
            ref={closeButton}
            className="icon-button dash__close"
            aria-label="Close menu"
            onClick={close}
          >
            <X size={18} />
          </button>
        </div>
        <SideNav onNavigate={close} />
        <div className="dash__side-foot">
          <EngineStatus />
          <Link to="/" className="dash__home">
            <ArrowLeft size={16} aria-hidden="true" />
            About AidOS
          </Link>
        </div>
      </aside>
      {menuOpen && <div className="dash__scrim" onClick={close} aria-hidden="true" />}

      {/* While the phone drawer is open, the page behind it is out of the tab order. */}
      <div className="dash__body" inert={menuOpen}>
        <header className="dash__top">
          <button
            ref={menuButton}
            type="button"
            className="icon-button dash__menu"
            aria-label="Open menu"
            aria-expanded={menuOpen}
            aria-controls="dash-sidebar"
            onClick={() => setMenuOpen(true)}
          >
            <Menu size={18} />
          </button>
          <p className="dash__title">{title}</p>
          <div className="dash__top-tools">
            <SyntheticBadge />
            <ScenarioSelector />
          </div>
        </header>
        <main id="dash-main" className="dash__main" tabIndex={-1}>
          <RouteErrorBoundary key={location.pathname}>
            <Outlet context={context} />
          </RouteErrorBoundary>
        </main>
      </div>
    </div>
  );
}
