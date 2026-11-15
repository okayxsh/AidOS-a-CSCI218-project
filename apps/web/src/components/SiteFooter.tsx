import { Link } from 'react-router';
import { Logo } from './ui/Logo';

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__grid">
        <div className="site-footer__brand">
          <Logo />
          <p>Explainable emergency resource allocation simulation.</p>
        </div>
        <nav aria-label="Footer" className="site-footer__nav">
          <div>
            <h2>Product</h2>
            <ul>
              <li>
                <a href="#how-it-works">How it works</a>
              </li>
              <li>
                <a href="#features">Features</a>
              </li>
              <li>
                <a href="#technology">Technology</a>
              </li>
              <li>
                <Link to="/dashboard">Dashboard</Link>
              </li>
            </ul>
          </div>
          <div>
            <h2>Project</h2>
            <ul>
              <li>
                <a href="#about">About</a>
              </li>
              <li>CSCI218 · UOWD</li>
              <li>Autumn 2026</li>
            </ul>
          </div>
        </nav>
      </div>
      <div className="container site-footer__legal">
        <p>
          Academic prototype. AidOS runs on synthetic scenarios only and is not a real dispatch,
          medical or humanitarian decision system. Human oversight is required for any real
          decision.
        </p>
      </div>
    </footer>
  );
}
