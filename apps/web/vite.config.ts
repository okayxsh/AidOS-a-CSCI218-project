import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// Tooling config only. Env vars (VITE_*) are read from the repository-root .env files.
export default defineConfig({
  plugins: [react()],
  envDir: '../..',
  server: {
    // The landing page imports the synthetic demo fixture from data/scenarios and the
    // engine's versioned fuzzy configuration (the same files the engine reads), so the dev
    // server may read them.
    fs: { allow: ['.', '../../data', '../api/aidos/config'] },
  },
});
