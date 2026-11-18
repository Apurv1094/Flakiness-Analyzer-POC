import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';

test.describe('JavaScript Alerts', () => {
  test('TC_022 - Accept JavaScript alert', async ({ page }) => {
    await page.goto(`${baseUrl}/javascript_alerts`);
    const dialogPromise = page.waitForEvent('dialog');
    await page.getByRole('button', { name: 'Click for JS Alert' }).click();
    const dialog = await dialogPromise;

    expect(dialog.type()).toBe('alert');
    expect(dialog.message()).toBe('I am a JS Alert');
    await dialog.accept();
    await expect(page.locator('#result')).toHaveText('You successfully clicked an alert');
  });

  test('TC_023 - Cancel JavaScript confirmation', async ({ page }) => {
    await page.goto(`${baseUrl}/javascript_alerts`);
    const dialogPromise = page.waitForEvent('dialog');
    await page.getByRole('button', { name: 'Click for JS Confirm' }).click();
    const dialog = await dialogPromise;

    expect(dialog.type()).toBe('confirm');
    expect(dialog.message()).toBe('I am a JS Confirm');
    await dialog.dismiss();
    await expect(page.locator('#result')).toHaveText('You clicked: Cancel');
  });

  test('TC_024 - Submit text through JavaScript prompt', async ({ page }) => {
    await page.goto(`${baseUrl}/javascript_alerts`);
    const dialogPromise = page.waitForEvent('dialog');
    await page.getByRole('button', { name: 'Click for JS Prompt' }).click();
    const dialog = await dialogPromise;

    expect(dialog.type()).toBe('prompt');
    expect(dialog.message()).toBe('I am a JS prompt');
    await dialog.accept('QA prompt value');
    await expect(page.locator('#result')).toHaveText('You entered: QA prompt value');
  });
});