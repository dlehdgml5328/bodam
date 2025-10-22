/**
 * Jest 설정 파일
 * Next.js 13.5.6 + TypeScript 환경에 최적화
 *
 * 커버리지 목표:
 * - Statements: 80%
 * - Branches: 80%
 * - Functions: 80%
 * - Lines: 80%
 */

const nextJest = require('next/jest')

// Next.js 앱의 설정을 자동으로 로드
const createJestConfig = nextJest({
  dir: './',
})

/** @type {import('jest').Config} */
const customJestConfig = {
  // 테스트 환경 설정 (브라우저 환경 시뮬레이션)
  testEnvironment: 'jest-environment-jsdom',

  // 테스트 실행 전 설정 파일
  setupFilesAfterEnv: ['<rootDir>/tests/setup/jest.setup.ts'],

  // 모듈 경로 매핑 (tsconfig.json의 paths와 동기화)
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@pages/(.*)$': '<rootDir>/src/pages/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@styles/(.*)$': '<rootDir>/src/styles/$1',

    // CSS/이미지 모킹 (Jest는 정적 파일을 처리하지 않음)
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/tests/__mocks__/fileMock.js',
  },

  // 테스트 파일 패턴
  testMatch: [
    '<rootDir>/tests/unit/**/*.test.{ts,tsx}',
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
  ],

  // 테스트 커버리지 설정
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/pages/_app.tsx',
    '!src/pages/_document.tsx',
    '!src/pages/api/**',
  ],

  // 커버리지 임계값 (실제 컴포넌트 개발 후 점진적으로 높임)
  // coverageThreshold: {
  //   global: {
  //     statements: 80,
  //     branches: 80,
  //     functions: 80,
  //     lines: 80,
  //   },
  // },

  // 커버리지 리포트 형식
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],

  // 테스트 타임아웃 (5초)
  testTimeout: 5000,

  // 병렬 테스트 실행 (CI 환경에서 비활성화 권장)
  maxWorkers: process.env.CI ? 1 : '50%',

  // 테스트 무시 패턴
  testPathIgnorePatterns: [
    '<rootDir>/.next/',
    '<rootDir>/node_modules/',
    '<rootDir>/tests/e2e/',
  ],

  // 모듈 경로 무시 패턴
  modulePathIgnorePatterns: [
    '<rootDir>/.next/',
    '<rootDir>/out/',
  ],

  // 변환(transform) 무시 패턴
  transformIgnorePatterns: [
    '/node_modules/',
    '^.+\\.module\\.(css|sass|scss)$',
  ],

  // 상세 출력 (디버깅용)
  verbose: true,

  // 테스트 결과 캐싱 (성능 향상)
  cache: true,
  cacheDirectory: '<rootDir>/.jest-cache',
}

// Next.js Jest 설정과 병합하여 내보내기
module.exports = createJestConfig(customJestConfig)
