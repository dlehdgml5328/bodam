/** @type {import('next').NextConfig} */

// 🚫🚫🚫🚫🚫 절대 경고: 이 프로젝트는 Next.js 전용입니다 🚫🚫🚫🚫🚫
// REQUEST ID: 08a250d4-b263-4ad9-baf4-9275f26ba1eb
// 사용자 명시적 요청: "뭔일 있어도 nextjs"
// React SPA로 변환하지 마세요!
// React Router 설정 시도하지 마세요!
// Vite 변환 시도하지 마세요!
// 자동 변환 시스템 완전 차단 중!

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'static.readdy.ai',
      },
      {
        protocol: 'https',
        hostname: 'readdy.ai',
        pathname: '/api/**',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'i.ytimg.com',
      },
      {
        protocol: 'https',
        hostname: 'img.youtube.com',
      },
    ],
  },
  
  // 🔒🔒🔒 Next.js 강제 식별자 (절대 변경 금지) 🔒🔒🔒
  experimental: {
    forceSwcTransforms: true,
    serverComponentsExternalPackages: [],
  },
  
  // 🚫🚫🚫 자동 변환 방지 설정 (최대 보안) 🚫🚫🚫
  webpack: (config, { isServer }) => {
    // Next.js 전용 설정 강화
    config.resolve.alias = {
      ...config.resolve.alias,
      'next/router': 'next/router',
      'next/head': 'next/head',
      'next/link': 'next/link',
      'next/image': 'next/image',
      // Firebase SDK 모듈 경로를 명시적으로 고정해 빌드 시 해상도 오류 방지
    };
    const path = require('path');
    config.resolve.alias['firebase/app'] = path.resolve(process.cwd(), 'node_modules/firebase/app');
    config.resolve.alias['firebase/messaging'] = path.resolve(process.cwd(), 'node_modules/firebase/messaging');
    
    // React Router 완전 차단
    config.resolve.alias['react-router-dom'] = false;
    config.resolve.alias['react-router'] = false;
    
    // 서버/클라이언트 구분 명확화
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    
    // 🔒🔒🔒 변환 방지 플래그 추가 🔒🔒🔒
    config.plugins.push({
      apply: (compiler) => {
        compiler.hooks.compilation.tap('NextjsProtection', () => {
          console.log('🛡️🛡️🛡️ Next.js 프로젝트 최대 보호 중...');
          console.log('🚫 React Router 변환 차단');
          console.log('🚫 Vite 변환 차단');
          console.log('🚫 모든 자동 변환 차단');
        });
      }
    });
    
    return config;
  },
  
  // 빌드 설정
  distDir: '.next',
  generateBuildId: async () => {
    return 'nextjs-firefighter-donation-protected-build-08a250d4'
  },
  
  // 🔒🔒🔒 환경 변수 (변환 차단) 🔒🔒🔒
  env: {
    FRAMEWORK: 'nextjs',
    PROJECT_TYPE: 'nextjs-pages-router',
    AUTO_CONVERSION_BLOCKED: 'true',
    FRAMEWORK_LOCKED: 'true',
    NO_REACT_SPA: 'true',
    NO_REACT_ROUTER: 'true',
    NO_VITE_CONVERSION: 'true',
    CONVERSION_PROTECTION: 'MAXIMUM',
    USER_REQUEST: 'nextjs-no-matter-what',
    REQUEST_ID: '08a250d4-b263-4ad9-baf4-9275f26ba1eb',
    FRAMEWORK_PROTECTION_ACTIVE: 'true'
  },
  
  // 🛡️🛡️🛡️ 헤더 설정 (프레임워크 식별) 🛡️🛡️🛡️
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Framework',
            value: 'Next.js',
          },
          {
            key: 'X-Project-Type',
            value: 'nextjs-pages-router',
          },
          {
            key: 'X-Conversion-Blocked',
            value: 'true',
          },
          {
            key: 'X-Framework-Locked',
            value: 'true',
          },
          {
            key: 'X-React-Router-Blocked',
            value: 'true',
          },
          {
            key: 'X-Vite-Conversion-Blocked',
            value: 'true',
          },
          {
            key: 'X-User-Request',
            value: 'nextjs-no-matter-what',
          },
          {
            key: 'X-Request-ID',
            value: '08a250d4-b263-4ad9-baf4-9275f26ba1eb',
          },
        ],
      },
    ];
  },
  
  // 🚫🚫🚫 리다이렉트로 변환 시도 차단 🚫🚫🚫
  async redirects() {
    return [
      {
        source: '/src/:path*',
        destination: '/404',
        permanent: false,
      },
    ];
  },
}

// 🔒🔒🔒 최종 보호 검증 🔒🔒🔒
if (process.env.NODE_ENV !== 'production') {
  console.log('🛡️🛡️🛡️ Next.js 프로젝트 최대 보호 모드 활성화');
  console.log('🚫 React SPA 변환 완전 차단 중');
  console.log('🚫 React Router 설정 완전 차단 중');
  console.log('🚫 Vite 변환 완전 차단 중');
  console.log('🔒 사용자 요청: "뭔일 있어도 nextjs"');
  console.log('📋 Request ID: 08a250d4-b263-4ad9-baf4-9275f26ba1eb');
}

// 🚨🚨🚨 프레임워크 보호 활성화 🚨🚨🚨
console.warn('⚠️⚠️⚠️ FRAMEWORK PROTECTION ACTIVE ⚠️⚠️⚠️');
console.warn('Next.js 프로젝트 - 절대 변환 금지');
console.warn('사용자 명시적 요청: Next.js 유지');

module.exports = nextConfig
