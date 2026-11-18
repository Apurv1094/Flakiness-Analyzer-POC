import { test, expect } from '@playwright/test';

const inventoryUrl = 'https://www.saucedemo.com/inventory.html';
const backpackDescription =
  'carry.allTheThings() with the sleek, streamlined Sly Pack that melds uncompromising style with unequaled laptop and tablet protection.';

async function signIn(page: import('@playwright/test').Page) {
  await page.goto('https://www.saucedemo.com/');
  await page.locator('[data-test="username"]').fill('standard_user');
  await page.locator('[data-test="password"]').fill('secret_sauce');
  await page.locator('[data-test="login-button"]').click();
  await expect(page).toHaveURL(inventoryUrl);
}

test.describe('Product listing, details, and sorting', () => {
  test('PRODUCT_TC_001 - Default product listing shows all six products', async ({ page }) => {
    // 1. Sign in with a fresh browser context and open the inventory page.
    await signIn(page);

    // Verify the Products heading, default A-to-Z products, prices, and Add to cart actions.
    await expect(page.getByText('Products', { exact: true })).toBeVisible();
    const products = page.locator('[data-test="inventory-item"]');
    await expect(products).toHaveCount(6);
    await expect(products.locator('[data-test="inventory-item-name"]')).toHaveText([
      'Sauce Labs Backpack',
      'Sauce Labs Bike Light',
      'Sauce Labs Bolt T-Shirt',
      'Sauce Labs Fleece Jacket',
      'Sauce Labs Onesie',
      'Test.allTheThings() T-Shirt (Red)',
    ]);
    await expect(products.locator('[data-test="inventory-item-price"]')).toHaveText([
      '$29.99',
      '$9.99',
      '$15.99',
      '$49.99',
      '$7.99',
      '$15.99',
    ]);

    for (const product of await products.all()) {
      await expect(product.getByRole('button', { name: 'Add to cart' })).toBeVisible();
    }
  });

  test('PRODUCT_TC_002 - Product detail shows backpack information and returns to catalog', async ({ page }) => {
    // 1. Sign in with a fresh browser context and open the inventory page.
    await signIn(page);
    await expect(page.locator('[data-test="item-4-title-link"]')).toBeVisible();
    // 2. Open the Sauce Labs Backpack product details.
    await page.locator('[data-test="item-4-title-link"]').click();
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory-item.html?id=4');
    await expect(page.getByText('Sauce Labs Backpack', { exact: true })).toBeVisible();
    await expect(page.getByRole('img', { name: 'Sauce Labs Backpack' })).toBeVisible();
    await expect(page.getByText(backpackDescription, { exact: true })).toBeVisible();
    await expect(page.getByText('$29.99', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add to cart' })).toBeVisible();

    // 3. Activate Back to products and verify the catalog returns.
    await page.getByRole('button', { name: 'Back to products' }).click();
    await expect(page).toHaveURL(inventoryUrl);
    await expect(page.getByText('Products', { exact: true })).toBeVisible();
    await expect(page.locator('[data-test="inventory-item"]')).toHaveCount(6);
  });

  test('PRODUCT_TC_003 - Adding a product from details updates its action and cart badge', async ({ page }) => {
    // 1. Sign in with a fresh browser context and open the backpack details page.
    await signIn(page);
    await page.locator('[data-test="item-4-title-link"]').click();
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory-item.html?id=4');
    await expect(page.getByRole('button', { name: 'Add to cart' })).toBeVisible();

    // 2. Add the backpack and verify the action changes and cart badge displays one item.
    await page.getByRole('button', { name: 'Add to cart' }).click();
    await expect(page.getByRole('button', { name: 'Remove' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cart, 1 items' })).toBeVisible();
  });
});
