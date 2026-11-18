import { test, expect } from '@playwright/test';

const inventoryUrl = 'https://www.saucedemo.com/inventory.html';
const ascendingNames = [
  'Sauce Labs Backpack',
  'Sauce Labs Bike Light',
  'Sauce Labs Bolt T-Shirt',
  'Sauce Labs Fleece Jacket',
  'Sauce Labs Onesie',
  'Test.allTheThings() T-Shirt (Red)',
];

async function signIn(page: import('@playwright/test').Page) {
  await page.goto('https://www.saucedemo.com/');
  await page.locator('[data-test="username"]').fill('standard_user');
  await page.locator('[data-test="password"]').fill('secret_sauce');
  await page.locator('[data-test="login-button"]').click();
  await expect(page).toHaveURL(inventoryUrl);
  await expect(page.getByRole('combobox', { name: 'Sort products' })).toBeVisible();
}

async function expectPricesInOrder(page: import('@playwright/test').Page, descending: boolean) {
  const priceTexts = await page.locator('[data-test="inventory-item-price"]').allTextContents();
  const prices = priceTexts.map((price) => Number(price.replace('$', '')));
  expect(prices).toHaveLength(6);

  for (let index = 1; index < prices.length; index += 1) {
    if (descending) {
      expect(prices[index]).toBeLessThanOrEqual(prices[index - 1]);
    } else {
      expect(prices[index]).toBeGreaterThanOrEqual(prices[index - 1]);
    }
  }
}

test.describe('Product listing, details, and sorting', () => {
  test('SORT_TC_001 - Products default to name ascending', async ({ page }) => {
    // 1. Sign in with a fresh browser context and verify the default sort control.
    await signIn(page);
    const sortControl = page.getByRole('combobox', { name: 'Sort products' });
    await expect(sortControl).toHaveValue('az');

    // 2. Verify visible product names appear in ascending order.
    await expect(page.locator('[data-test="inventory-item-name"]')).toHaveText(ascendingNames);
  });

  test('SORT_TC_002 - Name descending sort orders products Z to A', async ({ page }) => {
    // 1. Sign in with a fresh browser context.
    await signIn(page);

    // 2. Select Name (Z to A) and verify the visible product order.
    await page.getByRole('combobox', { name: 'Sort products' }).selectOption('za');
    await expect(page.getByRole('combobox', { name: 'Sort products' })).toHaveValue('za');
    await expect(page.locator('[data-test="inventory-item-name"]')).toHaveText([...ascendingNames].reverse());
  });

  test('SORT_TC_003 - Price ascending sort orders products low to high', async ({ page }) => {
    // 1. Sign in with a fresh browser context.
    await signIn(page);

    // 2. Select Price (low to high) and verify the specified sequence and numeric order.
    await page.getByRole('combobox', { name: 'Sort products' }).selectOption('lohi');
    await expect(page.getByRole('combobox', { name: 'Sort products' })).toHaveValue('lohi');
    await expect(page.locator('[data-test="inventory-item-name"]')).toHaveText([
      'Sauce Labs Onesie',
      'Sauce Labs Bike Light',
      'Sauce Labs Bolt T-Shirt',
      'Test.allTheThings() T-Shirt (Red)',
      'Sauce Labs Backpack',
      'Sauce Labs Fleece Jacket',
    ]);
    await expect(page.locator('[data-test="inventory-item-price"]')).toHaveText([
      '$7.99',
      '$9.99',
      '$15.99',
      '$15.99',
      '$29.99',
      '$49.99',
    ]);
    await expectPricesInOrder(page, false);
  });

  test('SORT_TC_004 - Price descending sort orders products high to low', async ({ page }) => {
    // 1. Sign in with a fresh browser context.
    await signIn(page);

    // 2. Select Price (high to low) and verify the specified sequence and numeric order.
    await page.getByRole('combobox', { name: 'Sort products' }).selectOption('hilo');
    await expect(page.getByRole('combobox', { name: 'Sort products' })).toHaveValue('hilo');
    await expect(page.locator('[data-test="inventory-item-name"]')).toHaveText([
      'Sauce Labs Fleece Jacket',
      'Sauce Labs Backpack',
      'Sauce Labs Bolt T-Shirt',
      'Test.allTheThings() T-Shirt (Red)',
      'Sauce Labs Bike Light',
      'Sauce Labs Onesie',
    ]);
    await expect(page.locator('[data-test="inventory-item-price"]')).toHaveText([
      '$49.99',
      '$29.99',
      '$15.99',
      '$15.99',
      '$9.99',
      '$7.99',
    ]);
    await expectPricesInOrder(page, true);
  });
});
