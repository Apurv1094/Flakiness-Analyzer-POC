import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';

const requiredLinks = ['Home', 'About', 'Contact Us', 'Portfolio'];

test.describe('Disappearing Elements', () => {
  test('TC_007 - Required navigation links render', async ({ page }) => {
    await page.goto(`${baseUrl}/disappearing_elements`);
    const navigation = page.locator('#content ul').first();

    for (const name of requiredLinks) {
      await expect(navigation.getByRole('link', { name, exact: true })).toBeVisible();
    }

    const gallery = navigation.getByRole('link', { name: 'Gallery', exact: true });
    if (await gallery.count()) {
      await expect(gallery).toHaveAttribute('href', '/gallery/');
    }
  });

  test('TC_008 - Home navigation returns to the index', async ({ page }) => {
    await page.goto(`${baseUrl}/disappearing_elements`);
    await page.locator('#content ul').first().getByRole('link', { name: 'Home', exact: true }).click();

    await expect(page).toHaveURL(`${baseUrl}/`);
    await expect(page.getByRole('heading', { name: 'Welcome to the-internet' })).toBeVisible();
  });

  test('TC_009 - Reload retains required links despite optional entry variation', async ({ page }) => {
    await page.goto(`${baseUrl}/disappearing_elements`);
    const navigation = page.locator('#content ul').first();
    for (const name of requiredLinks) {
      await expect(navigation.getByRole('link', { name, exact: true })).toBeVisible();
    }

    await page.reload();
    for (const name of requiredLinks) {
      await expect(navigation.getByRole('link', { name, exact: true })).toBeVisible();
    }
  });
});