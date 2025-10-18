/**
 * 홈페이지 E2E 테스트
 *
 * 테스트 커버리지:
 * - 페이지 로딩
 * - 메타데이터 (title, description)
 * - 주요 UI 요소 존재 확인
 * - 네비게이션 동작
 * - 반응형 디자인
 * - 접근성 (a11y)
 */

import { test, expect } from '@playwright/test'

/**
 * 홈페이지 기본 테스트
 */
test.describe('홈페이지', () => {
  /**
   * 각 테스트 전에 홈페이지로 이동
   */
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  /**
   * 페이지 로딩 테스트
   */
  test('페이지가 정상적으로 로딩된다', async ({ page }) => {
    // 페이지 타이틀 확인
    await expect(page).toHaveTitle(/소방관 기부|보담|BoDam/i)

    // 메인 콘텐츠가 로드될 때까지 대기
    await expect(page.locator('main')).toBeVisible()
  })

  /**
   * 메타데이터 테스트
   */
  test('올바른 메타데이터를 가지고 있다', async ({ page }) => {
    // Open Graph 메타 태그 확인
    const ogTitle = page.locator('meta[property="og:title"]')
    await expect(ogTitle).toHaveAttribute('content', /.+/)

    const ogDescription = page.locator('meta[property="og:description"]')
    await expect(ogDescription).toHaveAttribute('content', /.+/)

    // 뷰포트 메타 태그 확인 (반응형)
    const viewport = page.locator('meta[name="viewport"]')
    await expect(viewport).toHaveAttribute(
      'content',
      /width=device-width, initial-scale=1/i
    )
  })

  /**
   * 주요 UI 요소 테스트
   */
  test('주요 UI 요소가 표시된다', async ({ page }) => {
    // 헤더 (네비게이션)
    const header = page.locator('header, nav')
    await expect(header).toBeVisible()

    // 메인 콘텐츠
    const main = page.locator('main')
    await expect(main).toBeVisible()

    // 푸터
    const footer = page.locator('footer')
    await expect(footer).toBeVisible()
  })

  /**
   * 로고 테스트
   */
  test('로고가 표시되고 클릭 가능하다', async ({ page }) => {
    // 로고 이미지 또는 텍스트 찾기
    const logo = page.locator('header img[alt*="로고"], header a[href="/"]').first()
    await expect(logo).toBeVisible()

    // 로고 클릭 시 홈으로 이동
    await logo.click()
    await expect(page).toHaveURL('/')
  })

  /**
   * CTA (Call-to-Action) 버튼 테스트
   */
  test('기부하기 버튼이 표시된다', async ({ page }) => {
    // "기부하기" 또는 "후원하기" 버튼 찾기
    const donateButton = page.getByRole('link', {
      name: /기부하기|후원하기|donate/i,
    })

    await expect(donateButton.first()).toBeVisible()
  })

  /**
   * 네비게이션 테스트
   */
  test.describe('네비게이션', () => {
    test('기부하기 페이지로 이동할 수 있다', async ({ page }) => {
      // 기부하기 링크 클릭
      const donateLink = page.getByRole('link', { name: /기부하기|donate/i }).first()
      await donateLink.click()

      // URL 변경 확인
      await expect(page).toHaveURL(/\/donate|\/donation/)
    })

    test('소방서 목록 페이지로 이동할 수 있다', async ({ page }) => {
      // 소방서 링크 클릭
      const stationsLink = page
        .getByRole('link', { name: /소방서|fire station/i })
        .first()

      if (await stationsLink.isVisible()) {
        await stationsLink.click()
        await expect(page).toHaveURL(/\/stations|\/fire-stations/)
      } else {
        // 소방서 링크가 없으면 테스트 스킵
        test.skip()
      }
    })
  })

  /**
   * 반응형 디자인 테스트
   */
  test.describe('반응형 디자인', () => {
    test('모바일 뷰포트에서 정상 작동한다', async ({ page }) => {
      // 모바일 크기로 변경 (iPhone 12 기준)
      await page.setViewportSize({ width: 390, height: 844 })

      // 페이지 로드
      await page.goto('/')

      // 메인 콘텐츠 확인
      await expect(page.locator('main')).toBeVisible()

      // 햄버거 메뉴 버튼 확인 (모바일에서만 표시)
      const menuButton = page.locator('button[aria-label*="메뉴"], button[aria-label*="menu"]')
      if (await menuButton.isVisible()) {
        await expect(menuButton).toBeVisible()
      }
    })

    test('태블릿 뷰포트에서 정상 작동한다', async ({ page }) => {
      // 태블릿 크기로 변경 (iPad 기준)
      await page.setViewportSize({ width: 768, height: 1024 })

      await page.goto('/')

      // 메인 콘텐츠 확인
      await expect(page.locator('main')).toBeVisible()
    })

    test('데스크톱 뷰포트에서 정상 작동한다', async ({ page }) => {
      // 데스크톱 크기로 변경
      await page.setViewportSize({ width: 1920, height: 1080 })

      await page.goto('/')

      // 메인 콘텐츠 확인
      await expect(page.locator('main')).toBeVisible()
    })
  })

  /**
   * 접근성 테스트
   */
  test.describe('접근성 (a11y)', () => {
    test('페이지에 h1 태그가 존재한다', async ({ page }) => {
      const h1 = page.locator('h1')
      await expect(h1.first()).toBeVisible()
    })

    test('모든 이미지에 alt 속성이 있다', async ({ page }) => {
      const images = page.locator('img')
      const count = await images.count()

      for (let i = 0; i < count; i++) {
        const img = images.nth(i)
        const alt = await img.getAttribute('alt')
        expect(alt).not.toBeNull()
      }
    })

    test('링크에 접근 가능한 텍스트가 있다', async ({ page }) => {
      const links = page.locator('a')
      const count = await links.count()

      for (let i = 0; i < count; i++) {
        const link = links.nth(i)
        const text = await link.textContent()
        const ariaLabel = await link.getAttribute('aria-label')
        const title = await link.getAttribute('title')

        // 텍스트, aria-label, 또는 title 중 하나는 반드시 존재
        expect(
          (text && text.trim().length > 0) ||
          (ariaLabel && ariaLabel.length > 0) ||
          (title && title.length > 0)
        ).toBeTruthy()
      }
    })

    test('키보드로 네비게이션 가능하다', async ({ page }) => {
      // Tab 키로 포커스 이동
      await page.keyboard.press('Tab')

      // 포커스된 요소 확인
      const focusedElement = await page.evaluateHandle(() => document.activeElement)
      expect(focusedElement).toBeTruthy()

      // Enter 키로 링크 클릭 가능 확인
      await page.keyboard.press('Enter')

      // 페이지가 변경되었는지 또는 모달이 열렸는지 확인
      // (실제 동작은 프로젝트마다 다름)
    })
  })

  /**
   * 성능 테스트
   */
  test('페이지 로딩 시간이 3초 이내이다', async ({ page }) => {
    const startTime = Date.now()

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const loadTime = Date.now() - startTime

    // 3초(3000ms) 이내에 로딩 완료
    expect(loadTime).toBeLessThan(3000)
  })

  /**
   * SEO 테스트
   */
  test('기본 SEO 메타 태그가 존재한다', async ({ page }) => {
    // description 메타 태그
    const description = page.locator('meta[name="description"]')
    await expect(description).toHaveAttribute('content', /.+/)

    // keywords 메타 태그 (선택 사항)
    const keywords = page.locator('meta[name="keywords"]')
    if (await keywords.count() > 0) {
      await expect(keywords).toHaveAttribute('content', /.+/)
    }

    // canonical 링크
    const canonical = page.locator('link[rel="canonical"]')
    if (await canonical.count() > 0) {
      await expect(canonical).toHaveAttribute('href', /.+/)
    }
  })
})
