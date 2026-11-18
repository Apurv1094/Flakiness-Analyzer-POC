import { test, expect, type Page } from '@playwright/test';

const inventoryUrl = 'https://www.saucedemo.com/inventory.html';
const loginUrl = 'https://www.saucedemo.com/';

async function signIn(page: Page) {
  await page.goto(loginUrl);
  await page.locator('[data-test="username"]').fill('standard_user');
  await page.locator('[data-test="password"]').fill('secret_sauce');
  await page.locator('[data-test="login-button"]').click();
  await expect(page).toHaveURL(inventoryUrl);
}

async function logOut(page: Page) {
  await page.getByRole('button', { name: 'Open Menu' }).click();
  await expect(page.locator('[data-test="logout-sidebar-link"]')).toBeVisible();
  await page.locator('[data-test="logout-sidebar-link"]').click();
  await expect(page).toHaveURL(loginUrl);
}

test.describe('Logout functionality', () => {
  test('LOGOUT_TC_001 - Logout returns the user to the login page', async ({ page }) => {
    // 1. Sign in and open the navigation menu.
    await signIn(page);
    await page.getByRole('button', { name: 'Open Menu' }).click();

    // Verify Logout is available, then log out.
    const logoutItem = page.locator('[data-test="logout-sidebar-link"]');
    await expect(logoutItem).toBeVisible();
    await logoutItem.click();

    // Verify the root login page and its login controls.
    await expect(page).toHaveURL(loginUrl);
    await expect(page.getByRole('textbox', { name: 'Username' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Password' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
  });

  test('LOGOUT_TC_002 - Logged-out user cannot open inventory directly', async ({ page }) => {
    // 1. Sign in, log out, and directly request the protected inventory route.
    await signIn(page);
    await logOut(page);
    await page.goto(inventoryUrl);

    // Verify redirection to login and the observed access-restriction alert.
    await expect(page).toHaveURL(loginUrl);
    await expect(page.getByRole('alert')).toHaveText(
      "Epic sadface: You can only access '/inventory.html' when you are logged in.",
    );
  });

  test('LOGOUT_TC_003 - Cart contents persist after logout and re-login in the same context', async ({ page }) => {
    // 1. Sign in with an empty cart and add the backpack.
    await signIn(page);
    await expect(page.getByRole('button', { name: 'Cart, empty' })).toBeVisible();
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();
    await expect(page.getByRole('button', { name: 'Cart, 1 items' })).toBeVisible();

    // Log out and re-authenticate in this same isolated browser context.
    await logOut(page);
    await signIn(page);

    // Verify the backpack remains selected and the cart badge remains one.
    await expect(page.locator('[data-test="remove-sauce-labs-backpack"]')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cart, 1 items' })).toBeVisible();
  });
});
