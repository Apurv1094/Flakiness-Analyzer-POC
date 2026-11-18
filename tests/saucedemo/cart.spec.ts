import { test, expect, type Page, type Locator } from '@playwright/test';

const inventoryUrl = 'https://www.saucedemo.com/inventory.html';
const cartUrl = 'https://www.saucedemo.com/cart.html';

async function signInWithEmptyCart(page: Page) {
  await page.goto('https://www.saucedemo.com/');
  await page.locator('[data-test="username"]').fill('standard_user');
  await page.locator('[data-test="password"]').fill('secret_sauce');
  await page.locator('[data-test="login-button"]').click();
  await expect(page).toHaveURL(inventoryUrl);
  await expect(page.getByRole('button', { name: 'Cart, empty' })).toBeVisible();
}

async function addToCart(page: Page, productTestId: string) {
  await page.locator(`[data-test="add-to-cart-${productTestId}"]`).click();
}

async function openCart(page: Page) {
  await page.locator('[data-test="shopping-cart-link"]').click();
  await expect(page).toHaveURL(cartUrl);
}

function cartRows(page: Page): Locator {
  return page.locator('[data-test="cart-list"] [data-test="inventory-item"]');
}

function cartRow(page: Page, productName: string): Locator {
  return cartRows(page).filter({ has: page.getByRole('button', { name: `View details for ${productName}` }) });
}

async function expectCartRow(page: Page, productName: string, price: string) {
  const row = cartRow(page, productName);
  await expect(row).toHaveCount(1);
  await expect(row.locator('[data-test="item-quantity"]')).toHaveText('1');
  await expect(row.locator('[data-test="inventory-item-price"]')).toHaveText(price);
  await expect(row.getByRole('button', { name: 'Remove' })).toBeVisible();
}

test.describe('Shopping cart', () => {
  test('CART_TC_001 - Add one product and verify cart contents', async ({ page }) => {
    // 1. Sign in with an empty cart and verify the backpack is available to add.
    await signInWithEmptyCart(page);
    await expect(page.locator('[data-test="add-to-cart-sauce-labs-backpack"]')).toBeVisible();

    // 2. Add the backpack and open the cart.
    await addToCart(page, 'sauce-labs-backpack');
    await openCart(page);

    // Verify badge, exact cart row, price, quantity, and Remove action.
    await expect(page.getByRole('button', { name: 'Cart, 1 items' })).toBeVisible();
    await expect(cartRows(page)).toHaveCount(1);
    await expectCartRow(page, 'Sauce Labs Backpack', '$29.99');
  });

  test('CART_TC_002 - Multiple distinct products appear as separate cart rows', async ({ page }) => {
    // 1. Sign in with an empty cart and confirm both products are listed.
    await signInWithEmptyCart(page);
    await expect(page.locator('[data-test="inventory-item-sauce-labs-backpack-img"]')).toBeVisible();
    await expect(page.locator('[data-test="inventory-item-sauce-labs-bike-light-img"]')).toBeVisible();

    // 2. Add both products and open the cart.
    await addToCart(page, 'sauce-labs-backpack');
    await addToCart(page, 'sauce-labs-bike-light');
    await openCart(page);

    // Verify separate rows with each product's price and quantity.
    await expect(page.getByRole('button', { name: 'Cart, 2 items' })).toBeVisible();
    await expect(cartRows(page)).toHaveCount(2);
    await expectCartRow(page, 'Sauce Labs Backpack', '$29.99');
    await expectCartRow(page, 'Sauce Labs Bike Light', '$9.99');
  });

  test('CART_TC_003 - Removing one cart item preserves the other', async ({ page }) => {
    // 1. Sign in with an empty cart and add the backpack and Bike Light.
    await signInWithEmptyCart(page);
    await addToCart(page, 'sauce-labs-backpack');
    await addToCart(page, 'sauce-labs-bike-light');
    await openCart(page);
    await expect(cartRows(page)).toHaveCount(2);
    await expect(page.getByRole('button', { name: 'Cart, 2 items' })).toBeVisible();

    // 2. Remove Sauce Labs Bike Light from the cart.
    await cartRow(page, 'Sauce Labs Bike Light').locator('[data-test="remove-sauce-labs-bike-light"]').click();

    // Verify Bike Light is absent while Backpack remains at quantity one and the badge is one.
    await expect(cartRows(page)).toHaveCount(1);
    await expect(cartRow(page, 'Sauce Labs Bike Light')).toHaveCount(0);
    await expectCartRow(page, 'Sauce Labs Backpack', '$29.99');
    await expect(page.getByRole('button', { name: 'Cart, 1 items' })).toBeVisible();
  });

  test('CART_TC_004 - Removing the final item leaves an empty cart', async ({ page }) => {
    // 1. Sign in with an empty cart, add one backpack, and open the cart.
    await signInWithEmptyCart(page);
    await addToCart(page, 'sauce-labs-backpack');
    await openCart(page);
    await expect(cartRows(page)).toHaveCount(1);
    await expectCartRow(page, 'Sauce Labs Backpack', '$29.99');
    await expect(page.getByRole('button', { name: 'Cart, 1 items' })).toBeVisible();

    // 2. Remove the backpack from the cart.
    await cartRow(page, 'Sauce Labs Backpack').locator('[data-test="remove-sauce-labs-backpack"]').click();

    // Verify no rows or badge remain and both cart actions are still available.
    await expect(cartRows(page)).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Cart, empty' })).toBeVisible();
    await expect(page.locator('[data-test="shopping-cart-badge"]')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Continue Shopping' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Checkout' })).toBeVisible();
  });

  test('CART_TC_005 - Remove from product listing clears cart state', async ({ page }) => {
    // 1. Sign in with an empty cart and verify the backpack listing action.
    await signInWithEmptyCart(page);
    const backpack = page.locator('[data-test="inventory-item"]').filter({ has: page.getByText('Sauce Labs Backpack', { exact: true }) });
    await expect(backpack.locator('[data-test="add-to-cart-sauce-labs-backpack"]')).toBeVisible();

    // 2. Add the backpack, then activate its listing-level Remove action.
    await addToCart(page, 'sauce-labs-backpack');
    await expect(backpack.locator('[data-test="remove-sauce-labs-backpack"]')).toBeVisible();
    await backpack.locator('[data-test="remove-sauce-labs-backpack"]').click();

    // Verify the listing action is restored and the cart badge is absent.
    await expect(backpack.locator('[data-test="add-to-cart-sauce-labs-backpack"]')).toBeVisible();
    await expect(page.locator('[data-test="shopping-cart-badge"]')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Cart, empty' })).toBeVisible();
  });

  test('CART_TC_006 - A selected product has quantity one and cannot be duplicated by the add toggle', async ({ page }) => {
    // 1. Sign in with an empty cart and verify the backpack initially exposes Add to cart.
    await signInWithEmptyCart(page);
    const backpack = page.locator('[data-test="inventory-item"]').filter({ has: page.getByText('Sauce Labs Backpack', { exact: true }) });
    await expect(backpack.locator('[data-test="add-to-cart-sauce-labs-backpack"]')).toBeVisible();

    // 2. Add the backpack and inspect both its listing action and its cart row.
    await addToCart(page, 'sauce-labs-backpack');
    await expect(backpack.locator('[data-test="remove-sauce-labs-backpack"]')).toBeVisible();
    await expect(backpack.locator('[data-test="add-to-cart-sauce-labs-backpack"]')).toHaveCount(0);
    await openCart(page);
    await expect(page.getByRole('button', { name: 'Cart, 1 items' })).toBeVisible();
    await expect(cartRows(page)).toHaveCount(1);
    await expectCartRow(page, 'Sauce Labs Backpack', '$29.99');

    // Verify the cart has no quantity editor or increment/decrement controls.
    const cart = page.locator('[data-test="cart-list"]');
    await expect(cart.locator('input, select, [role="spinbutton"]')).toHaveCount(0);
    await expect(cart.getByRole('button', { name: /increase|decrease|increment|decrement|quantity/i })).toHaveCount(0);
  });
});
