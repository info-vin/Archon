import { Page } from '@playwright/test';

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
