/**
 * Jest 테스트 환경 설정 파일
 * 모든 테스트 실행 전에 자동으로 로드됨
 *
 * 주요 기능:
 * - @testing-library/jest-dom 매처 활성화
 * - 전역 모킹 설정
 * - 테스트 환경 변수 설정
 */

import '@testing-library/jest-dom'

/**
 * 환경 변수 모킹
 * Next.js 런타임 환경 변수를 테스트 환경에서 사용 가능하도록 설정
 */
process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY = 'test_ck_TEST_KEY_12345'
process.env.NEXT_PUBLIC_KAKAO_APP_KEY = 'test_kakao_key'

/**
 * window.matchMedia 모킹
 * 많은 컴포넌트가 반응형 디자인을 위해 matchMedia를 사용하므로 모킹 필요
 */
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

/**
 * IntersectionObserver 모킹
 * 무한 스크롤, 레이지 로딩 등에서 사용되는 API
 */
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
} as any

/**
 * ResizeObserver 모킹
 * 컴포넌트 크기 변화 감지에 사용되는 API
 */
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any

/**
 * fetch API 모킹 (선택 사항)
 * 실제 API 호출 대신 모킹된 응답을 반환
 */
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: async () => ({ success: true }),
    text: async () => 'OK',
    headers: new Headers(),
  })
) as jest.Mock

/**
 * 콘솔 에러 무시 (선택 사항)
 * React Testing Library의 예상된 경고를 숨기기 위해 사용
 */
const originalError = console.error
beforeAll(() => {
  console.error = (...args: any[]) => {
    // React의 예상된 에러 메시지 필터링
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
        args[0].includes('Warning: useLayoutEffect') ||
        args[0].includes('Not implemented: HTMLFormElement.prototype.submit'))
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})

/**
 * 테스트 타임아웃 전역 설정
 * 개별 테스트에서 오버라이드 가능
 */
jest.setTimeout(10000)

/**
 * 각 테스트 후 모든 모킹 초기화
 * 테스트 간 격리를 보장하기 위해 필요
 */
afterEach(() => {
  jest.clearAllMocks()
})
