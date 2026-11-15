import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
// Self-hosted fonts: the demo must work offline, with no external font requests.
import '@fontsource-variable/mona-sans';
import '@fontsource/instrument-serif/400-italic.css';
import '@fontsource-variable/jetbrains-mono';
import './styles/tokens.css';
import './styles/global.css';
import App from './app/App';

const root = document.getElementById('root');
if (!root) throw new Error('Missing #root element in index.html');

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
