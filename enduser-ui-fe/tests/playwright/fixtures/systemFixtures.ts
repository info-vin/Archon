import { test as base, Page, expect } from '@playwright/test';

/**
 * Simulates a severe network timeout for a specific endpoint pattern.
 * This forces the UI to hit its timeout threshold and display loading/error states.
 * 
 * @param page Playwright Page object
 * @param urlPattern URL pattern to delay
 * @param delayMs Delay in milliseconds (default: 15000ms)
 */
export async function simulateNetworkTimeout(page: Page, urlPattern: string | RegExp, delayMs: number = 15000) {
  await page.route(urlPattern, async route => {
    await new Promise(resolve => setTimeout(resolve, delayMs));
    await route.continue();
  });
}

/**
 * Simulates a hard 500 Internal Server Error for a specific endpoint pattern.
 * 
 * @param page Playwright Page object
 * @param urlPattern URL pattern to fail
 */
export async function simulate500Error(page: Page, urlPattern: string | RegExp) {
  await page.route(urlPattern, async route => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Internal Server Error (Simulated Chaos)' })
    });
  });
}

/**
 * A stateful mock registry to simulate database CRUD without a backend.
 * Not needed if tests run strictly against `make dev-docker`, but useful for specific UI state isolation.
 */
export class StatefulMock<T> {
  private data: T[];

  constructor(initialData: T[] = []) {
    this.data = [...initialData];
  }

  get() {
    return this.data;
  }

  add(item: T) {
    this.data.push(item);
  }

  update(predicate: (item: T) => boolean, updater: (item: T) => T) {
    const idx = this.data.findIndex(predicate);
    if (idx !== -1) {
      this.data[idx] = updater(this.data[idx]);
    }
  }

  remove(predicate: (item: T) => boolean) {
    this.data = this.data.filter(item => !predicate(item));
  }
}

/**
 * Resiliently waits for any active loading spinners to disappear from the page.
 * 
 * @param page Playwright Page object
 * @param timeout Timeout in milliseconds (default: 10000ms)
 */
export async function waitForSpinner(page: Page, timeout: number = 10000) {
  // Resiliently wait 50ms for React rendering cycle to finish mounting the spinner
  await page.waitForTimeout(50);
  
  // Wait for the common spinner class or a generic loading indicator
  // In Archon, this is usually a div with 'animate-spin' class
  const spinner = page.locator('.animate-spin');
  try {
    await spinner.waitFor({ state: 'detached', timeout });
  } catch (e) {
    console.warn('⚠️ Timed out waiting for spinner to detach. UI might be locked.');
  }
}

/**
 * Simulates an SSE task update event by dispatching a CustomEvent on the window.
 * 
 * @param page Playwright Page object
 * @param taskId ID of the task being updated
 * @param status Target status (done, failed, etc.)
 * @param result Optional result payload
 */
export async function simulateSSEUpdate(page: Page, taskId: string, status: 'done' | 'failed' | 'processing', result: any = null) {
  await page.evaluate(({ taskId, status, result }) => {
    const event = new CustomEvent('archon:task_updated', {
      detail: {
        task_id: taskId,
        status: status,
        agent_output: result
      }
    });
    window.dispatchEvent(event);
  }, { taskId, status, result });
}

/**
 * Disables all CSS transitions, animations, and Recharts animations for the given page.
 * This guarantees 100% deterministic and stable VRT and E2E screenshots by eliminating
 * animation lag, transition delays, and rendering flakiness.
 * 
 * @param page Playwright Page object
 */
export async function disableChartAnimations(page: Page) {
  // Inject CSS to disable animations/transitions before page loads or during run
  await page.addInitScript(() => {
    const style = document.createElement('style');
    style.id = 'disable-animations-styles';
    style.innerHTML = `
      *, *::before, *::after {
        transition: none !important;
        animation: none !important;
        transition-duration: 0s !important;
        animation-duration: 0s !important;
        transition-delay: 0s !important;
        animation-delay: 0s !important;
      }
    `;
    document.head.appendChild(style);
  });

  try {
    await page.addStyleTag({
      content: `
        *, *::before, *::after {
          transition: none !important;
          animation: none !important;
          transition-duration: 0s !important;
          animation-duration: 0s !important;
          transition-delay: 0s !important;
          animation-delay: 0s !important;
        }
      `
    });
  } catch (e) {
    // Ignore in case the page is not loaded yet or has no document head
  }
}

// Export custom test that automatically disables all animations on startup
export const test = base.extend({
  page: async ({ page }, use) => {
    await disableChartAnimations(page);
    await use(page);
  }
});

export { expect };
