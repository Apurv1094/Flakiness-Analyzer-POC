import { test, expect, type Page } from '@playwright/test';

const loginUrl = 'https://www.saucedemo.com/';
const inventoryUrl = `${loginUrl}inventory.html`;
const cartUrl = `${loginUrl}cart.html`;
const checkoutInfoUrl = `${loginUrl}checkout-step-one.html`;
const checkoutOverviewUrl = `${loginUrl}checkout-step-two.html`;
const checkoutCompleteUrl = `${loginUrl}checkout-complete.html`;

async function signIn(page: Page) {
  await page.goto(loginUrl);
  await page.locator('[data-test="username"]').fill('standard_user');
  await page.locator('[data-test="password"]').fill('secret_sauce');
  await page.locator('[data-test="login-button"]').click();
  await expect(page).toHaveURL(inventoryUrl);
}

async function addBackpack(page: Page) {
  await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();
  await expect(page.getByRole('button', { name: 'Cart, 1 items' })).toBeVisible();
}

async function openCheckoutInfo(page: Page, withBackpack: boolean) {
  await signIn(page);
  if (withBackpack) {
    await addBackpack(page);
  }
  await page.locator('[data-test="shopping-cart-link"]').click();
  await expect(page).toHaveURL(cartUrl);
  await page.locator('[data-test="checkout"]').click();
  await expect(page).toHaveURL(checkoutInfoUrl);
}

async function fillCheckoutInfo(page: Page, firstName: string, lastName: string, postalCode: string) {
  await page.locator('[data-test="firstName"]').fill(firstName);
  await page.locator('[data-test="lastName"]').fill(lastName);
  await page.locator('[data-test="postalCode"]').fill(postalCode);
}

async function expectCheckoutForm(page: Page) {
  await expect(page.getByText('Checkout: Your Information', { exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'First Name' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Last Name' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Zip/Postal Code' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Continue' })).toBeVisible();
}

test.describe('Checkout and order completion', () => {
  test('CHECKOUT_TC_001 - Empty checkout form requires first name', async ({ page }) => {
    // 1. Sign in, add the backpack, open the cart, and select Checkout.
    await openCheckoutInfo(page, true);

    // Verify the form and submit it with all fields empty.
    await expectCheckoutForm(page);
    await page.locator('[data-test="continue"]').click();

    // Verify the checkout form remains open and the first-name validation is shown.
    await expect(page).toHaveURL(checkoutInfoUrl);
    await expect(page.getByRole('alert')).toHaveText('Error: First Name is required');
  });

  test('CHECKOUT_TC_002 - Checkout requires last name', async ({ page }) => {
    // 1. Sign in, add the backpack, open the cart, and select Checkout.
    await openCheckoutInfo(page, true);

    // Enter only the first name and submit checkout information.
    await expectCheckoutForm(page);
    await page.locator('[data-test="firstName"]').fill('Avery');
    await page.locator('[data-test="continue"]').click();

    // Verify the checkout form remains open and the last-name validation is shown.
    await expect(page).toHaveURL(checkoutInfoUrl);
    await expect(page.getByRole('alert')).toHaveText('Error: Last Name is required');
  });

  test('CHECKOUT_TC_003 - Checkout requires postal code', async ({ page }) => {
    // 1. Sign in, add the backpack, open the cart, and select Checkout.
    await openCheckoutInfo(page, true);

    // Enter first and last names, leaving postal code empty.
    await expectCheckoutForm(page);
    await page.locator('[data-test="firstName"]').fill('Avery');
    await page.locator('[data-test="lastName"]').fill('Tester');
    await page.locator('[data-test="continue"]').click();

    // Verify the checkout form remains open and the postal-code validation is shown.
    await expect(page).toHaveURL(checkoutInfoUrl);
    await expect(page.getByRole('alert')).toHaveText('Error: Postal Code is required');
  });

  test('CHECKOUT_TC_004 - Valid checkout information produces the expected overview totals', async ({ page }) => {
    // 1. Sign in, add the backpack, open the cart, and confirm Checkout is available.
    await signIn(page);
    await addBackpack(page);
    await page.locator('[data-test="shopping-cart-link"]').click();
    await expect(page).toHaveURL(cartUrl);
    await expect(page.locator('[data-test="cart-list"] [data-test="inventory-item"]')).toHaveCount(1);
    await expect(page.getByRole('button', { name: 'Checkout' })).toBeVisible();

    // Enter the valid customer details and continue to the overview.
    await page.locator('[data-test="checkout"]').click();
    await expectCheckoutForm(page);
    await fillCheckoutInfo(page, 'Avery', 'Tester', '10001');
    await page.locator('[data-test="continue"]').click();

    // Verify the overview product, payment, shipping, total amounts, and controls.
    await expect(page).toHaveURL(checkoutOverviewUrl);
    const overviewRows = page.locator('[data-test="cart-list"] [data-test="inventory-item"]');
    await expect(overviewRows).toHaveCount(1);
    await expect(overviewRows.locator('[data-test="inventory-item-name"]')).toHaveText('Sauce Labs Backpack');
    await expect(overviewRows.locator('[data-test="item-quantity"]')).toHaveText('1');
    await expect(overviewRows.locator('[data-test="inventory-item-price"]')).toHaveText('$29.99');
    await expect(page.getByText('SauceCard #31337', { exact: true })).toBeVisible();
    await expect(page.getByText('Free Pony Express Delivery!', { exact: true })).toBeVisible();
    await expect(page.getByText('Item total: $29.99', { exact: true })).toBeVisible();
    await expect(page.getByText('Tax: $2.40', { exact: true })).toBeVisible();
    await expect(page.getByText('Total: $32.39', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Finish' })).toBeVisible();
  });

  test('CHECKOUT_TC_005 - Canceling checkout information returns to cart and preserves items', async ({ page }) => {
    // 1. Sign in, add the backpack, open the cart, and select Checkout.
    await openCheckoutInfo(page, true);
    await expectCheckoutForm(page);

    // 2. Cancel checkout information.
    await page.locator('[data-test="cancel"]').click();

    // Verify return to cart with the backpack still present at quantity one and badge one.
    await expect(page).toHaveURL(cartUrl);
    const cartRows = page.locator('[data-test="cart-list"] [data-test="inventory-item"]');
    await expect(cartRows).toHaveCount(1);
    await expect(cartRows.locator('[data-test="inventory-item-name"]')).toHaveText('Sauce Labs Backpack');
    await expect(cartRows.locator('[data-test="item-quantity"]')).toHaveText('1');
    await expect(cartRows.locator('[data-test="inventory-item-price"]')).toHaveText('$29.99');
    await expect(page.getByRole('button', { name: 'Cart, 1 items' })).toBeVisible();
  });

  test('CHECKOUT_TC_006 - Finishing checkout confirms the order and clears the cart', async ({ page }) => {
    // 1. Sign in, add the backpack, and complete the checkout information.
    await signIn(page);
    await expect(page.locator('[data-test="inventory-item-sauce-labs-backpack-img"]')).toBeVisible();
    await addBackpack(page);
    await page.locator('[data-test="shopping-cart-link"]').click();
    await expect(page).toHaveURL(cartUrl);
    await page.locator('[data-test="checkout"]').click();
    await expectCheckoutForm(page);
    await fillCheckoutInfo(page, 'Avery', 'Tester', '10001');
    await page.locator('[data-test="continue"]').click();
    await expect(page).toHaveURL(checkoutOverviewUrl);

    // 2. Finish the order and verify confirmation and cleared cart state.
    await page.locator('[data-test="finish"]').click();
    await expect(page).toHaveURL(checkoutCompleteUrl);
    await expect(page.getByRole('heading', { name: 'Thank you for your order!' })).toBeVisible();
    await expect(page.getByText('Your order has been dispatched, and will arrive just as fast as the pony can get there!', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cart, empty' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Back Home' })).toBeVisible();
  });

  test('CHECKOUT_TC_007 - Empty-cart checkout shows zero totals and completes', async ({ page }) => {
    // 1. Sign in without adding products and open Checkout from the empty cart.
    await openCheckoutInfo(page, false);
    await expect(page.getByRole('button', { name: 'Cart, empty' })).toBeVisible();
    await expect(page.locator('[data-test="cart-list"] [data-test="inventory-item"]')).toHaveCount(0);

    // Enter the specified information and continue to the observed empty-cart overview.
    await fillCheckoutInfo(page, 'Zero', 'Items', '00000');
    await page.locator('[data-test="continue"]').click();

    // Verify no product rows and the exact zero totals, then complete the observed flow.
    await expect(page).toHaveURL(checkoutOverviewUrl);
    await expect(page.locator('[data-test="cart-list"] [data-test="inventory-item"]')).toHaveCount(0);
    await expect(page.getByText('Item total: $0', { exact: true })).toBeVisible();
    await expect(page.getByText('Tax: $0.00', { exact: true })).toBeVisible();
    await expect(page.getByText('Total: $0.00', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Finish' })).toBeVisible();
    await page.locator('[data-test="finish"]').click();
    await expect(page).toHaveURL(checkoutCompleteUrl);
    await expect(page.getByRole('heading', { name: 'Thank you for your order!' })).toBeVisible();
  });
});
