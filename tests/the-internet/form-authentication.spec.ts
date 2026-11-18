import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';

async function login(page: import('@playwright/test').Page, username: string, password: string) {
  await page.goto(`${baseUrl}/login`);
  await page.getByRole('textbox', { name: 'Username' }).fill(username);
  await page.getByRole('textbox', { name: 'Password' }).fill(password);
  await page.getByRole('button', { name: /Login/ }).click();
}

test.describe('Form Authentication', () => {
  test('TC_013 - Valid credentials open the secure area', async ({ page }) => {
    await login(page, 'tomsmith', 'SuperSecretPassword!');

    await expect(page).toHaveURL(`${baseUrl}/secure`);
    await expect(page.locator('#flash')).toContainText('You logged into a secure area!');
    await expect(page.getByRole('link', { name: 'Logout' })).toBeVisible();
  });

  test('TC_014 - Invalid username is rejected', async ({ page }) => {
    await login(page, 'wrong_user', 'not_a_valid_password');

    await expect(page).toHaveURL(`${baseUrl}/login`);
    await expect(page.locator('#flash')).toContainText('Your username is invalid!');
  });

  test('TC_015 - Invalid password is rejected', async ({ page }) => {
    await login(page, 'tomsmith', 'incorrect_password');

    await expect(page).toHaveURL(`${baseUrl}/login`);
    await expect(page.locator('#flash')).toContainText('Your password is invalid!');
  });
});