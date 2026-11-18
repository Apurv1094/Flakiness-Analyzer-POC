import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';

test.describe('Challenging DOM', () => {
  test('TC_010 - Table exposes expected columns and ten data rows', async ({ page }) => {
    await page.goto(`${baseUrl}/challenging_dom`);
    const table = page.getByRole('table');

    await expect(table.getByRole('columnheader')).toHaveText([
      'Lorem', 'Ipsum', 'Dolor', 'Sit', 'Amet', 'Diceret', 'Action',
    ]);
    await expect(table.locator('tbody tr')).toHaveCount(10);
  });

  test('TC_011 - Edit action targets its row without removing table data', async ({ page }) => {
    await page.goto(`${baseUrl}/challenging_dom`);
    const table = page.getByRole('table');
    const firstRow = table.locator('tbody tr').first();

    await firstRow.locator('a[href="#edit"]').click();
    await expect(page).toHaveURL(/#edit$/);
    await expect(table.locator('tbody tr')).toHaveCount(10);
  });

  test('TC_012 - Delete action link target is row-scoped', async ({ page }) => {
    await page.goto(`${baseUrl}/challenging_dom`);
    const table = page.getByRole('table');
    const firstRow = table.locator('tbody tr').first();

    await firstRow.locator('a[href="#delete"]').click();
    await expect(page).toHaveURL(/#delete$/);
    await expect(table).toBeVisible();
    await expect(table.locator('tbody tr')).toHaveCount(10);
  });
});