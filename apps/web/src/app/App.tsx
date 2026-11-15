import { useEffect } from 'react';
import { BrowserRouter, useLocation } from 'react-router';
import { AppRoutes } from './Router';

/** New routes start at the top; in-page anchors (#how-it-works) keep native scrolling. */
function ScrollManager() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (!hash) window.scrollTo(0, 0);
    if (pathname === '/') document.title = 'AidOS · Explainable emergency resource allocation';
  }, [pathname, hash]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollManager />
      <AppRoutes />
    </BrowserRouter>
  );
}
