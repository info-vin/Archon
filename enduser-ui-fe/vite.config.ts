/// <reference types="vitest" />
import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { existsSync } from 'fs';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');

    // Logic ported from archon-ui-main to handle Docker environment
    const isDocker = process.env.DOCKER_ENV === 'true' || existsSync('/.dockerenv');
    const internalHost = 'archon-server'; // Docker service name for internal communication
    const externalHost = process.env.HOST || 'localhost'; // Host for external access
    const proxyHost = isDocker ? internalHost : externalHost;
    const port = process.env.ARCHON_SERVER_PORT || env.ARCHON_SERVER_PORT || '8181';

    return {
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, './src'),
        }
      },
      server: {
        host: '0.0.0.0',
        port: 5173,
        allowedHosts: true,
        hmr: isDocker ? false : undefined,
        proxy: {
          '/api': {
            target: `http://${proxyHost}:${port}`,
            changeOrigin: true,
            secure: false,
            configure: (proxy, options) => {
              proxy.on('error', (err, req, res) => {
                console.log(`🚨 [VITE PROXY ERROR][enduser-ui-fe]: ${err.message}`);
                console.log('   Target:', `http://${proxyHost}:${port}`);
                console.log('   Request:', req.url);
              });
              proxy.on('proxyReq', (proxyReq, req, res) => {
                console.log(`🔄 [VITE PROXY][enduser-ui-fe]: Forwarding: ${req.method} ${req.url} to http://${proxyHost}:${port}${req.url}`);
              });
            }
          },
          '/socket.io': {
            target: `http://${proxyHost}:${port}`,
            changeOrigin: true,
            ws: true
          }
        }
      },
      build: {
        emptyOutDir: true,
      },
      preview: {
        host: '0.0.0.0',
        port: 5173,
        strictPort: true,
      },
      test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './test/setup.ts',
        exclude: ['tests/playwright/**', 'node_modules', 'tests/e2e/**'],
        testTimeout: 10000,
        hookTimeout: 10000,
      }
    };
});