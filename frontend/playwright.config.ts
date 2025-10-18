/**
 * Playwright 설정 파일
 * E2E 테스트를 위한 크로스 브라우저 테스트 환경 설정
 *
 * 지원 브라우저:
 * - Chromium (Chrome, Edge)
 * - Firefox
 * - Webkit (Safari)
 */

import { defineConfig, devices } from '@playwright/test'

/**
 * 환경 변수 설정
 * CI 환경에서는 BASE_URL을 명시적으로 설정
 */
const PORT = process.env.PORT || 3000
const BASE_URL = process.env.BASE_URL || `http://localhost:${PORT}`

export default defineConfig({
  // 테스트 디렉토리
  testDir: './tests/e2e',

  // 테스트 타임아웃 (30초)
  timeout: 30 * 1000,

  // 각 테스트 전후 expect 타임아웃 (5초)
  expect: {
    timeout: 5000,
  },

  // 실패한 테스트만 재시도 (최대 2회)
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,

  // 병렬 워커 수 (CI에서는 1개, 로컬에서는 CPU 코어 수의 절반)
  workers: process.env.CI ? 1 : undefined,

  // 리포터 설정
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'playwright-report/results.json' }],
    ['list'],
  ],

  // 모든 테스트에서 공유되는 설정
  use: {
    // 기본 URL (모든 테스트에서 사용)
    baseURL: BASE_URL,

    // 추적 설정 (실패 시에만 추적 기록)
    trace: 'on-first-retry',

    // 스크린샷 설정 (실패 시에만)
    screenshot: 'only-on-failure',

    // 비디오 설정 (실패 시에만)
    video: 'retain-on-failure',

    // 액션 타임아웃
    actionTimeout: 10 * 1000,

    // 네비게이션 타임아웃
    navigationTimeout: 15 * 1000,
  },

  // 프로젝트별 브라우저 설정
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
    },

    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1280, height: 720 },
      },
    },

    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1280, height: 720 },
      },
    },

    // 모바일 테스트 (선택 사항)
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],

  // 로컬 개발 서버 자동 시작
  webServer: {
    command: 'npm run dev',
    port: Number(PORT),
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
    stdout: 'ignore',
    stderr: 'pipe',
  },

  // 출력 디렉토리
  outputDir: 'test-results/',

  // 스냅샷 경로 설정
  snapshotDir: './tests/e2e/__snapshots__',

  // 전역 설정 파일 (선택 사항)
  // globalSetup: require.resolve('./tests/setup/global-setup.ts'),
  // globalTeardown: require.resolve('./tests/setup/global-teardown.ts'),
})
