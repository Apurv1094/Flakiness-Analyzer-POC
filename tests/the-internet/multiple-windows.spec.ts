import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';

test.describe('Multiple Windows', () => {
  test('TC_028 - Click Here opens a new window', async ({ page }) => {
    await page.goto(`${baseUrl}/windows`);
    const popupPromise = page.waitForEvent('popup');
    await page.getByRole('link', { name: 'Click Here' }).click();
    const popup = await popupPromise;

    await expect(popup).toHaveURL(`${baseUrl}/windows/new`);
    await expect(popup.getByRole('heading', { name: 'New Window' })).toBeVisible();
  });

  test('TC_029 - Parent remains on the opening page after popup opens', async ({ page }) => {
    await page.goto(`${baseUrl}/windows`);
    const popupPromise = page.waitForEvent('popup');
    await page.getByRole('link', { name: 'Click Here' }).click();
    const popup = await popupPromise;

    await expect(popup.getByRole('heading', { name: 'New Window' })).toBeVisible();
    await expect(page).toHaveURL(`${baseUrl}/windows`);
    await expect(page.getByRole('heading', { name: 'Opening a new window' })).toBeVisible();
  });

  test('TC_030 - New Window route is directly accessible', async ({ page }) => {
    await page.goto(`${baseUrl}/windows/new`);

    await expect(page.getByRole('heading', { name: 'New Window' })).toBeVisible();
    await expect(page).toHaveURL(`${baseUrl}/windows/new`);
  });
});