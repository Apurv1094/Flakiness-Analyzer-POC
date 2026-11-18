import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';

test.describe('Dynamic Loading', () => {
  test('TC_001 - Existing hidden element becomes visible', async ({ page }) => {
    await page.goto(`${baseUrl}/dynamic_loading/1`);
    const result = page.getByText('Hello World!', { exact: true });
    await expect(result).not.toBeVisible();

    // await page.getByRole('button', { name: 'Start' }).click();
    await page.locator("//button[text()='Start']").click();
    await expect(result).toBeVisible({timeout: 10000});
    await expect(result).toHaveText('Hello World!');
  });

  test('TC_002 - Dynamically inserted result appears after Start', async ({ page }) => {
    await page.goto(`${baseUrl}/dynamic_loading/2`);
    const result = page.getByText('Hello World!', { exact: true });
    await expect(result).toHaveCount(0);

    await page.getByRole('button', { name: 'Start' }).click();
    await expect(result).toBeVisible();
    await expect(result).toHaveText('Hello World!');
  });

  test('TC_003 - Loading indicator transitions to the final result', async ({ page }) => {
    await page.goto(`${baseUrl}/dynamic_loading/2`);
    await page.getByRole('button', { name: 'Start' }).click();

    const result = page.getByText('Hello World!', { exact: true });
    await expect(result).toBeVisible();
    await expect(page.locator('#loading')).toBeHidden();
  });
});