import { test, expect } from '@playwright/test';

test.describe('Login functionality', () => {
  test('LOGIN_TC_001 - Standard user logs in successfully', async ({ page }) => {
    // 1. Start from a fresh logged-out login page.
    await page.goto('https://www.saucedemo.com/');

    // 2. Fill Username and Password with the specified values, then activate Login.
    await page.locator('[data-test="username"]').fill('standard_user');
    await page.locator('[data-test="password"]').fill('secret_sauce');
    await page.locator('[data-test="login-button"]').click();

    // Verify navigation to the inventory page and the six visible catalog items.
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory.html');
    await expect(page.getByText('Products', { exact: true })).toBeVisible();
    await expect(page.locator('[data-test="inventory-item"]')).toHaveCount(6);
  });

  test('LOGIN_TC_002 - Empty username and password are rejected', async ({ page }) => {
    // 1. Start from a fresh login page with both credentials empty.
    await page.goto('https://www.saucedemo.com/');

    // 2. Activate Login without entering either value.
    await page.locator('[data-test="login-button"]').click();

    // Verify the form stays on the login page and reports the required username.
    await expect(page).toHaveURL('https://www.saucedemo.com/');
    await expect(page.getByRole('alert')).toHaveText('Epic sadface: Username is required');
  });

  test('LOGIN_TC_003 - Missing password is rejected', async ({ page }) => {
    // 1. Start from a fresh login page.
    await page.goto('https://www.saucedemo.com/');

    // 2. Fill Username only and activate Login.
    await page.locator('[data-test="username"]').fill('standard_user');
    await page.locator('[data-test="login-button"]').click();

    // Verify the form stays on the login page and reports the required password.
    await expect(page).toHaveURL('https://www.saucedemo.com/');
    await expect(page.getByRole('alert')).toHaveText('Epic sadface: Password is required');
  });

  test('LOGIN_TC_004 - Invalid credentials are rejected', async ({ page }) => {
    // 1. Start from a fresh login page.
    await page.goto('https://www.saucedemo.com/');

    // 2. Enter a known username and invalid password, then activate Login.
    await page.locator('[data-test="username"]').fill('standard_user');
    await page.locator('[data-test="password"]').fill('invalid_password');
    await page.locator('[data-test="login-button"]').click();

    // Verify the form stays on the login page and reports the credential mismatch.
    await expect(page).toHaveURL('https://www.saucedemo.com/');
    await expect(page.getByRole('alert')).toHaveText(
      'Epic sadface: Username and password do not match any user in this service',
    );
  });

  test('LOGIN_TC_005 - Locked-out user cannot log in', async ({ page }) => {
    // 1. Start from a fresh login page.
    await page.goto('https://www.saucedemo.com/');

    // 2. Enter the locked-out username and documented password, then activate Login.
    await page.locator('[data-test="username"]').fill('locked_out_user');
    await page.locator('[data-test="password"]').fill('secret_sauce');
    await page.locator('[data-test="login-button"]').click();

    // Verify the form stays on the login page and reports the locked-out user.
    await expect(page).toHaveURL('https://www.saucedemo.com/');
    await expect(page.getByRole('alert')).toHaveText(
      'Epic sadface: Sorry, this user has been locked out.',
    );
  });
});
