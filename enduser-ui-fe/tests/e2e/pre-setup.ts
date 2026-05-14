import { vi } from 'vitest';

/**
 * SECTION 0: CRITICAL BROWSER POLYFILLS
 * Using Object.defineProperty to lock down globals before React ever runs.
 */

// Inject default test API URL so URL parsing doesn't fail
vi.stubEnv('VITE_API_URL', 'http://localhost');

const mockMatchMedia = vi.fn().mockImplementation(query => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(), 
  removeListener: vi.fn(), 
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}));

// Physical lock on global and window
Object.defineProperty(global, 'matchMedia', {
    writable: true,
    value: mockMatchMedia
});

if (typeof window !== 'undefined') {
    Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: mockMatchMedia
    });
}

// Ensure other globals don't crash components
const noop = () => {};
if (typeof window !== 'undefined') {
    window.scrollTo = noop;
    (window as any).alert = noop;
    (window as any).confirm = () => true;
}

if (typeof Element !== 'undefined') {
    Element.prototype.scrollIntoView = noop;
}

if (typeof HTMLDialogElement !== 'undefined' && !HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function(this: HTMLDialogElement) {
        this.setAttribute('open', '');
    };
    HTMLDialogElement.prototype.close = function(this: HTMLDialogElement) {
        this.removeAttribute('open');
    };
}
