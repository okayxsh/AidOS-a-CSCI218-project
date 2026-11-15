import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config';

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      include: ['src/**/*.test.{ts,tsx}'],
      setupFiles: ['./src/test/setup.ts'],
      css: false,
      // Lazy routes, Recharts and large fixtures make the first test of a file slow on a
      // loaded machine. These limits only bound waiting; assertions still fail immediately.
      testTimeout: 20_000,
    },
  }),
);
