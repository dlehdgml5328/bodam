import { test, expect } from '@playwright/test';

test('홈 페이지가 소방서 검색 UI를 표시한다', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page.getByRole('heading', { name: /커피 한 잔/ })).toBeVisible();
  await expect(page.getByPlaceholder('예) 강남소방서')).toBeVisible();
});
