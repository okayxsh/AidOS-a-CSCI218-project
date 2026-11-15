import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router';
import Landing from '../pages/Landing';
import NotFound, { DashboardNotFound } from '../pages/NotFound';

// The dashboard (and Recharts) load only when a dashboard route is opened,
// so the landing page stays light and renders without the backend.
const DashboardLayout = lazy(() => import('../pages/DashboardLayout'));
const Overview = lazy(() => import('../pages/Overview'));
const Scenarios = lazy(() => import('../pages/Scenarios'));
const Inventory = lazy(() => import('../pages/Inventory'));
const Allocate = lazy(() => import('../pages/Allocate'));
const Simulate = lazy(() => import('../pages/Simulate'));
const Evaluate = lazy(() => import('../pages/Evaluate'));

function RouteFallback() {
  return (
    <div className="route-fallback" role="status">
      <span className="visually-hidden">Loading…</span>
    </div>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<Overview />} />
          <Route path="scenarios" element={<Scenarios />} />
          <Route path="inventory" element={<Inventory />} />
          <Route path="allocate" element={<Allocate />} />
          <Route path="simulate" element={<Simulate />} />
          <Route path="evaluate" element={<Evaluate />} />
          <Route path="*" element={<DashboardNotFound />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
