import { test, expect } from '@playwright/test';

const baseUrl = 'https://the-internet.herokuapp.com';
const entries = (page: import('@playwright/test').Page) => page.locator('#content > .row');

async function getEntryTexts(page: import('@playwright/test').Page): Promise<string[]> {
  const texts = await entries(page).allTextContents();
  return texts.map((text) => text.trim());
}

test.describe('Dynamic Content', () => {
  test('TC_016 - Dynamic content renders three text entries', async ({ page }) => {
    await page.goto(`${baseUrl}/dynamic_content`);
    await expect(entries(page)).toHaveCount(3);

    const texts = await getEntryTexts(page);
    expect(texts).toHaveLength(3);
    for (const text of texts) {
      expect(text.length).toBeGreaterThan(0);
    }
  });

  test('TC_017 - Content changes after refresh', async ({ page }) => {
    await page.goto(`${baseUrl}/dynamic_content`);
    const initialTexts = await getEntryTexts(page);
    expect(initialTexts).toHaveLength(3);
    expect(initialTexts.every((text) => text.length > 0)).toBe(true);

    await page.reload();
    await expect(entries(page)).toHaveCount(3);
    const refreshedTexts = await getEntryTexts(page);
    expect(refreshedTexts).toHaveLength(3);
    expect(refreshedTexts.some((text) => text.length > 0)).toBe(true);
    expect(refreshedTexts).not.toEqual(initialTexts);
  });

  test('TC_018 - Static-content query mode opens', async ({ page }) => {
    await page.goto(`${baseUrl}/dynamic_content`);
    await page.getByRole('link', { name: 'click here' }).click();

    await expect(page).toHaveURL(/\/dynamic_content\?with_content=static$/);
    await expect(page.getByRole('heading', { name: 'Dynamic Content' })).toBeVisible();
    await expect(entries(page)).toHaveCount(3);
  });
});