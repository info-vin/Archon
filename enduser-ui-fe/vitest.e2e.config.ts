// vitest.e2e.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

// This is a self-contained configuration for E2E tests.
// It does not merge the base vite.config.ts because the base config is a function,
// which is incompatible with mergeConfig. This defines the minimum necessary
// config for running React-based E2E tests with Vitest.

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    // Use an array to load BOTH the global setup file and the E2E-specific one.
    // The order is important: global setup first, then E2E-specific setup.
    setupFiles: ['./test/setup.ts', './tests/e2e/e2e.setup.ts'],
    
    // Only run tests located in the tests/e2e/ directory for this config
    include: ['tests/e2e/**/*.spec.tsx'],

    // E2E tests might take longer, so we can set a higher timeout
    testTimeout: 15000,
    hookTimeout: 15000,

    // Ensure globals are still available
    globals: true,

    // Use the same jsdom environment
    environment: 'jsdom',

    // Global setup script for E2E tests (e.g., database reset)
    globalSetup: './tests/e2e/globalSetup.ts',
  },
});
