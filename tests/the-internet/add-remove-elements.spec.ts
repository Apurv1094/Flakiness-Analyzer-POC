import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';

test.describe('Add/Remove Elements', () => {
  test('TC_019 - Add Element creates a Delete control', async ({ page }) => {
    await page.goto(`${baseUrl}/add_remove_elements/`);
    await page.getByRole('button', { name: 'Add Element' }).click();
    await expect(page.getByRole('button', { name: 'Delete' })).toHaveCount(1);
  });

  test('TC_020 - Multiple added elements have independent Delete controls', async ({ page }) => {
    await page.goto(`${baseUrl}/add_remove_elements/`);
    const addButton = page.getByRole('button', { name: 'Add Element' });
    for (let index = 0; index < 3; index += 1) {
      await addButton.click();
    }

    await expect(page.getByRole('button', { name: 'Delete' })).toHaveCount(3);
  });

  test('TC_021 - Delete removes one added control', async ({ page }) => {
    await page.goto(`${baseUrl}/add_remove_elements/`);
    const addButton = page.getByRole('button', { name: 'Add Element' });
    await addButton.click();
    await addButton.click();
    const deleteButtons = page.getByRole('button', { name: 'Delete' });
    await expect(deleteButtons).toHaveCount(2);

    await deleteButtons.first().click();
    await expect(deleteButtons).toHaveCount(1);
  });
});