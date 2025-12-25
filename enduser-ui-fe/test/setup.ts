import '@testing-library/jest-dom';
import { server } from '../src/mocks/server';
import { vi } from 'vitest';
import { Task, TaskStatus, TaskPriority } from '../src/types';

// Mock for window.alert to prevent "Not implemented" errors in jsdom
vi.stubGlobal('alert', vi.fn());

// Mock for window.matchMedia, which is not implemented in jsdom
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Establish API mocking for any remaining HTTP requests before all tests.
beforeAll(() => server.listen());

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests.
afterEach(() => {
  server.resetHandlers();
  // also reset mock function calls
  vi.clearAllMocks();
});

// Clean up after the tests are finished.
afterAll(() => server.close());
