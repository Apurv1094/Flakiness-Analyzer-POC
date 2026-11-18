import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';

test.describe('Dynamic Controls', () => {
  test('TC_004 - Remove and restore the checkbox', async ({ page }) => {
    await page.goto(`${baseUrl}/dynamic_controls`);
    const checkbox = page.getByRole('checkbox');
    await expect(checkbox).toBeVisible();

    await page.getByRole('button', { name: 'Remove' }).click();
    await expect(checkbox).toHaveCount(0);
    await expect(page.getByText("It's gone!")).toBeVisible();

    await page.getByRole('button', { name: 'Add' }).click();
    await expect(checkbox).toBeVisible();
    await expect(page.getByText("It's back!")).toBeVisible();
  });

  test('TC_005 - Enable input and enter text', async ({ page }) => {
    await page.goto(`${baseUrl}/dynamic_controls`);
    const input = page.locator('input[type="text"]');
    await expect(input).toBeDisabled();

    await page.getByRole('button', { name: 'Enable' }).click();
    await expect(input).toBeEnabled();
    await input.fill('Playwright sample');
    await expect(input).toHaveValue('Playwright sample');
  });

  test('TC_006 - Disable an enabled input', async ({ page }) => {
    await page.goto(`${baseUrl}/dynamic_controls`);
    const input = page.locator('input[type="text"]');
    await page.getByRole('button', { name: 'Enable' }).click();
    await expect(input).toBeEnabled();

    await page.getByRole('button', { name: 'Disable' }).click();
    await expect(input).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Enable' })).toBeVisible();
  });
});