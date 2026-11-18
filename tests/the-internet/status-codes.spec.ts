import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';

test.describe('Status Codes', () => {
  test('TC_025 - Status Codes 200 endpoint responds successfully', async ({ page }) => {
    const response = await page.goto(`${baseUrl}/status_codes/200`);
    expect(response?.status()).toBe(200);
    await expect(page.getByText('This page returned a 200 status code.')).toBeVisible();
    await expect(page.getByRole('link', { name: 'here' })).toHaveAttribute('href', '/status_codes');
  });

  test('TC_026 - Status Codes 301 endpoint returns its status response', async ({ page }) => {
    const endpoint = `${baseUrl}/status_codes/301`;
    const originalResponse = await page.request.get(endpoint, { maxRedirects: 0 });
    expect(originalResponse.status()).toBe(301);
    await originalResponse.dispose();

    const navigationResponse = await page.goto(endpoint);
    expect(navigationResponse?.status()).toBe(301);
    await expect(page.getByText('This page returned a 301 status code.')).toBeVisible();
    await expect(page.getByRole('link', { name: 'here' })).toHaveAttribute('href', '/status_codes');
  });

  test('TC_027 - Status Codes 404 endpoint shows not-found response', async ({ page }) => {
    const response = await page.goto(`${baseUrl}/status_codes/404`);
    expect(response?.status()).toBe(404);
    await expect(page.getByText('This page returned a 404 status code.')).toBeVisible();
    await expect(page.getByRole('link', { name: 'here' })).toHaveAttribute('href', '/status_codes');
  });
});