# BoDam 인프라·SEO·성능 종합 가이드

## 목차
1. [인프라 구성 검증 요약](#1-인프라-구성-검증-요약)
2. [SEO 체크리스트](#2-seo-체크리스트)
3. [추가 성능 향상 방안](#3-추가-성능-향상-방안)

---

## 1. 인프라 구성 검증 요약

### 1.1 전체 아키텍처 개요

BoDam 프로젝트는 백엔드와 프론트엔드를 분리한 하이브리드 배포 전략을 사용합니다:

```
┌─────────────────────────────────────────────────────────────┐
│                         사용자                               │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│  Vercel CDN  │          │  DigitalOcean│
│  (Frontend)  │          │    (Backend) │
└──────────────┘          └──────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
            ┌─────────────┐          ┌─────────────┐
            │   Nginx     │          │    Kong     │
            │   (HTTPS,   │──────────│  Gateway    │
            │   Static)   │          │  (API GW)   │
            └─────────────┘          └──────┬──────┘
                                            │
                                ┌───────────┴───────────┐
                                ▼                       ▼
                        ┌──────────────┐       ┌──────────────┐
                        │  FastAPI     │       │  PostgreSQL  │
                        │  (1-3 pods)  │       │  + Redis     │
                        │  HPA/CA      │       │              │
                        └──────────────┘       └──────────────┘
```

### 1.2 DigitalOcean 백엔드 인프라

#### ✅ Nginx 설정 (`/home/eugene/bodam/infra/k8s/nginx/nginx-configmap.yaml`)

**HTTPS 및 TLS 종료:**
- TLS 1.2/1.3 지원
- cert-manager를 통한 Let's Encrypt 자동 인증서 관리
- HTTP → HTTPS 자동 리다이렉트 (301)
- HSTS 헤더 적용 (max-age=31536000)

```nginx
# HTTPS Server
server {
    listen 443 ssl http2;
    server_name api.bodam.example app.bodam.example;

    # TLS Configuration
    ssl_certificate /etc/nginx/tls/tls.crt;
    ssl_certificate_key /etc/nginx/tls/tls.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

**정적 파일 제공:**
- `/static/`: 1년 캐시, immutable
- `/_next/static/`: Next.js 정적 에셋 (1년 캐시)
- 이미지/폰트: 1년 캐시
- HTML 파일: 1시간 캐시 (must-revalidate)

```nginx
# Static files location
location /static/ {
    alias /usr/share/nginx/html/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;  # I/O 최적화
}
```

**Gzip 압축:**
- 압축 레벨 6 (균형잡힌 성능)
- JSON, JavaScript, CSS, XML, 폰트 등 지원

```nginx
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript
           application/json application/javascript application/xml+rss;
```

**Kong Gateway 연동:**
- Upstream 연결: `kong-gateway.default.svc.cluster.local:8000`
- Keep-Alive 연결 풀 (32개)
- `/api/*` 경로를 Kong으로 프록시

```nginx
upstream kong_upstream {
    server kong-gateway.default.svc.cluster.local:8000;
    keepalive 32;
}

location /api/ {
    proxy_pass http://kong_upstream;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

#### ✅ Kong Gateway 설정 (`/home/eugene/bodam/infra/k8s/kong/kong-config.yaml`)

**API 라우팅:**
- 선언적 구성 (Declarative Config, `_format_version: "3.0"`)
- 백엔드 서비스: `http://172.17.0.1:8080` (FastAPI)

**주요 기능:**
1. **JWT 인증**: `/api/donations`, `/api/users/profile`, `/api/admin/*`
2. **Rate Limiting**:
   - Auth endpoints: 10 req/min, 100 req/hour
   - Donations: 100 req/min, 1000 req/hour
   - Admin: 200 req/min
3. **CORS**: `https://app.bodam.example`, `https://admin.bodam.example`
4. **Request Tracing**: X-Request-ID (UUID) 자동 추가
5. **WebSocket 지원**: `/api/ws` (실시간 알림)

```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 100
      hour: 1000
      policy: local

  - name: jwt
    config:
      secret_is_base64: false
      claims_to_verify:
        - exp
```

#### ✅ HPA (Horizontal Pod Autoscaler)

**설정 요약 (`/home/eugene/bodam/infra/k8s/backend/backend-hpa.yaml`):**
- **최소 Replica**: 1
- **최대 Replica**: 3
- **CPU 임계값**: 60% (기존 70%에서 조정)
- **메모리 임계값**: 70% (기존 80%에서 조정)

**스케일링 정책:**
```yaml
# Scale Up: 30초 안정화, 100% 증가 (1→2→3)
scaleUp:
  stabilizationWindowSeconds: 30
  policies:
    - type: Percent
      value: 100
      periodSeconds: 30

# Scale Down: 3분 안정화, 50% 감소 (3→2→1)
scaleDown:
  stabilizationWindowSeconds: 180
  policies:
    - type: Percent
      value: 50
      periodSeconds: 60
```

#### ✅ Cluster Autoscaler (CA)

**DigitalOcean 노드 자동 확장:**
- 파일 위치: `/home/eugene/bodam/infra/k8s/cluster-autoscaler/autoscaler-config.yaml`
- Pod Pending 시 노드 자동 추가
- 유휴 노드 자동 제거 (10분 후)

### 1.3 Vercel 프론트엔드 배포

#### ✅ CI/CD 파이프라인 (`/home/eugene/bodam/.github/workflows/frontend-ci-cd.yml`)

**배포 전략:**
- **wonuk 브랜치**: Preview 환경 (Vercel Preview)
- **donghee 브랜치**: Production 환경 (Vercel Production)

**빌드 프로세스:**
1. ESLint 검사
2. TypeScript 타입 검사
3. Jest 단위 테스트 (커버리지)
4. Playwright E2E 테스트
5. Next.js 빌드 검증
6. Vercel 배포
7. Lighthouse CI (Production만)

**Vercel CDN 활용:**
- 정적 파일 자동 CDN 배포
- 엣지 캐싱
- 이미지 최적화 (Next.js Image)

```yaml
- name: Vercel 배포 (Production)
  run: |
    url=$(vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }})
    echo "production_url=$url" >> $GITHUB_OUTPUT
```

### 1.4 성능 최적화 적용 현황

#### ✅ 백엔드 성능 개선

**uvloop 적용 (`/home/eugene/bodam/backend/src/main.py`):**
```python
# uvloop 설정 (asyncio 이벤트 루프를 uvloop으로 교체하여 성능 향상)
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
```
- 예상 성능 향상: asyncio 대비 2-4배 빠른 I/O

**orjson 적용:**
```python
from fastapi.responses import ORJSONResponse

app = FastAPI(
    title="BoDam API",
    default_response_class=ORJSONResponse  # 표준 JSONResponse 대신 ORJSONResponse 사용
)
```
- 예상 성능 향상: JSON 직렬화/역직렬화 2-3배 개선

**DB Connection Pool (`/home/eugene/bodam/backend/src/database/connection.py`):**
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,              # 기본 연결 수
    max_overflow=20,           # 추가 연결 허용
    pool_recycle=3600,         # 1시간마다 재생성
    pool_pre_ping=True,        # 연결 유효성 검증
    pool_timeout=0.4,          # 대기 시간 400ms
)
```

### 1.5 인프라 검증 결론

| 구성 요소 | 상태 | 비고 |
|---------|------|------|
| ✅ Nginx HTTPS | 정상 | TLS 1.2/1.3, HSTS, cert-manager |
| ✅ Nginx 정적파일 | 정상 | 1년 캐시, Gzip 압축 레벨 6 |
| ✅ Kong Gateway | 정상 | JWT, Rate Limiting, CORS |
| ✅ HPA | 정상 | 1-3 Pods, CPU 60%, Memory 70% |
| ✅ Cluster Autoscaler | 정상 | DigitalOcean 노드 자동 확장 |
| ✅ Vercel CDN | 정상 | Next.js 빌드, 엣지 캐싱 |
| ✅ uvloop | 적용 완료 | AsyncIO 성능 2-4배 향상 |
| ✅ orjson | 적용 완료 | JSON 성능 2-3배 향상 |
| ✅ DB Pool | 최적화 완료 | pool_size=10, max_overflow=20 |

**주의사항:**
- 프론트엔드 정적파일은 Vercel CDN이 제공 (Nginx는 백엔드 정적 에셋만)
- Nginx의 `/static/`, `/_next/static/`은 백엔드 컨테이너 내부 파일 서빙용
- 실제 사용자 트래픽은 Vercel → (API 호출 시) DigitalOcean Nginx → Kong → FastAPI

---

## 2. SEO 체크리스트

### 2.1 필수 항목 (Must Have)

SEO를 고려했다고 말할 수 있는 최소 요구사항입니다. 이 항목들이 누락되면 검색 엔진 노출이 크게 저하됩니다.

#### 2.1.1 메타 태그 (Meta Tags)

**왜 필요한가?**
- Google, Naver 검색 결과 제목/설명 표시
- 소셜 미디어 공유 시 썸네일 이미지 표시
- 페이지 콘텐츠 요약 (검색 랭킹 영향)

**구현 위치:** `frontend/src/app/layout.tsx` (전역) 또는 각 페이지의 `metadata` export

**현재 상태:**
```tsx
// /home/eugene/bodam/frontend/src/app/layout.tsx (현재 구현)
export const metadata: Metadata = {
  title: '보담 - 소방관 기부 플랫폼',
  description: '소방관들에게 따뜻한 커피와 마음을 전해주세요',
  icons: {
    icon: 'https://static.readdy.ai/image/...png',
  },
};
```

**개선 필요 사항:**
```tsx
// frontend/src/app/layout.tsx (개선안)
export const metadata: Metadata = {
  title: {
    default: '보담 - 소방관 기부 플랫폼',
    template: '%s | 보담',  // 페이지별 제목 자동 추가
  },
  description: '소방관들에게 따뜻한 커피와 마음을 전해주세요. 기부금은 소방서에 직접 전달됩니다.',
  keywords: ['소방관', '기부', '후원', '소방서', '사회공헌'],
  authors: [{ name: 'BoDam Team' }],

  // Open Graph (Facebook, KakaoTalk)
  openGraph: {
    type: 'website',
    locale: 'ko_KR',
    url: 'https://bodam.example',
    siteName: '보담',
    title: '보담 - 소방관 기부 플랫폼',
    description: '소방관들에게 따뜻한 커피와 마음을 전해주세요',
    images: [
      {
        url: 'https://bodam.example/og-image.jpg',
        width: 1200,
        height: 630,
        alt: '보담 소방관 기부',
      },
    ],
  },

  // Twitter Card
  twitter: {
    card: 'summary_large_image',
    title: '보담 - 소방관 기부 플랫폼',
    description: '소방관들에게 따뜻한 커피와 마음을 전해주세요',
    images: ['https://bodam.example/twitter-image.jpg'],
  },

  // Verification
  verification: {
    google: 'google-site-verification-code',
    other: {
      'naver-site-verification': 'naver-verification-code',
    },
  },
};
```

**페이지별 메타 태그 추가:**
```tsx
// frontend/src/app/(public)/donations/page.tsx
export const metadata: Metadata = {
  title: '기부하기',
  description: '소방서를 선택하고 기부금을 전달하세요',
  openGraph: {
    title: '기부하기 - 보담',
    description: '소방서를 선택하고 기부금을 전달하세요',
  },
};
```

#### 2.1.2 robots.txt

**왜 필요한가?**
- 검색 엔진 크롤러에게 수집 허용/차단 경로 지시
- `/admin`, `/api` 등 불필요한 경로 차단
- sitemap.xml 위치 알림

**구현 위치:** `frontend/public/robots.txt`

**코드 예시:**
```txt
# frontend/public/robots.txt
User-agent: *
Allow: /
Disallow: /admin
Disallow: /api
Disallow: /mypage

# Sitemap location
Sitemap: https://bodam.example/sitemap.xml

# Specific bots
User-agent: Googlebot
Allow: /

User-agent: Yeti
Allow: /
```

#### 2.1.3 sitemap.xml

**왜 필요한가?**
- 검색 엔진이 페이지 구조를 빠르게 파악
- 새 페이지 색인 속도 향상
- 우선순위/업데이트 빈도 지시

**구현 위치:** `frontend/src/app/sitemap.ts` (Next.js 동적 생성)

**코드 예시:**
```tsx
// frontend/src/app/sitemap.ts
import { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://bodam.example';

  // 정적 페이지
  const staticPages = [
    '',
    '/donations',
    '/regions',
    '/donation-ranking',
    '/login',
    '/signup',
  ].map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: route === '' ? 1 : 0.8,
  }));

  // 동적 페이지 (예: 소방서 상세)
  // TODO: DB에서 소방서 ID 목록 가져오기
  const fireStations = [1, 2, 3].map((id) => ({
    url: `${baseUrl}/fire-station-detail/${id}`,
    lastModified: new Date(),
    changeFrequency: 'weekly' as const,
    priority: 0.6,
  }));

  return [...staticPages, ...fireStations];
}
```

#### 2.1.4 구조화된 데이터 (JSON-LD Schema.org)

**왜 필요한가?**
- Google 검색 결과에 리치 스니펫 표시 (별점, 가격, 이벤트 정보 등)
- 검색 엔진이 콘텐츠 의미를 정확히 이해
- CTR (클릭률) 향상

**구현 위치:** 각 페이지 컴포넌트에 `<script type="application/ld+json">`

**코드 예시:**
```tsx
// frontend/src/app/(public)/page.tsx (홈페이지)
export default function HomePage() {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: '보담',
    url: 'https://bodam.example',
    logo: 'https://bodam.example/logo.png',
    description: '소방관 기부 플랫폼',
    sameAs: [
      'https://www.facebook.com/bodam',
      'https://www.instagram.com/bodam',
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      {/* 페이지 콘텐츠 */}
    </>
  );
}

// frontend/src/app/(public)/fire-station-detail/[id]/page.tsx
export default function FireStationPage({ params }: { params: { id: string } }) {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'Place',
    name: '서울 중부소방서',
    address: {
      '@type': 'PostalAddress',
      addressLocality: '서울',
      addressRegion: '중구',
      postalCode: '04511',
    },
    geo: {
      '@type': 'GeoCoordinates',
      latitude: 37.5665,
      longitude: 126.9780,
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      {/* 페이지 콘텐츠 */}
    </>
  );
}
```

#### 2.1.5 시맨틱 HTML

**왜 필요한가?**
- 검색 엔진이 콘텐츠 구조를 이해
- 접근성 (스크린 리더) 향상
- SEO 랭킹에 긍정적 영향

**구현 위치:** 모든 페이지 컴포넌트

**잘못된 예:**
```tsx
<div>
  <div>제목</div>
  <div>본문</div>
</div>
```

**올바른 예:**
```tsx
<article>
  <header>
    <h1>보담 - 소방관 기부 플랫폼</h1>
    <p>따뜻한 마음을 전해주세요</p>
  </header>

  <section>
    <h2>기부 방법</h2>
    <p>소방서를 선택하고 기부금을 전달할 수 있습니다.</p>
  </section>

  <aside>
    <h3>최근 기부 내역</h3>
    <ul>
      <li>서울 중부소방서: 10,000원</li>
    </ul>
  </aside>

  <footer>
    <small>&copy; 2025 BoDam</small>
  </footer>
</article>
```

**HTML5 시맨틱 태그 활용:**
- `<header>`: 페이지 헤더
- `<nav>`: 내비게이션
- `<main>`: 주요 콘텐츠
- `<article>`: 독립적인 콘텐츠 (뉴스 기사, 블로그 글)
- `<section>`: 콘텐츠 섹션
- `<aside>`: 부가 정보 (사이드바)
- `<footer>`: 푸터

#### 2.1.6 이미지 alt 속성

**왜 필요한가?**
- Google 이미지 검색 노출
- 시각 장애인 접근성
- 이미지 로드 실패 시 대체 텍스트

**구현 위치:** 모든 `<img>`, `<Image>` 태그

**잘못된 예:**
```tsx
<Image src="/firefighter.jpg" width={500} height={300} />
```

**올바른 예:**
```tsx
<Image
  src="/firefighter.jpg"
  width={500}
  height={300}
  alt="화재 현장에서 구조 활동 중인 소방관"
  loading="lazy"  // 레이지 로딩
/>
```

#### 2.1.7 페이지 속도 최적화 (Core Web Vitals)

**왜 필요한가?**
- Google 검색 랭킹 주요 지표 (2021년부터)
- 사용자 이탈률 감소
- 전환율 향상

**측정 지표:**
- **LCP (Largest Contentful Paint)**: < 2.5초 (Good)
- **FID (First Input Delay)**: < 100ms (Good)
- **CLS (Cumulative Layout Shift)**: < 0.1 (Good)

**구현 방법:**
1. **Next.js Image 컴포넌트 사용** (자동 최적화)
2. **폰트 최적화** (`font-display: swap`)
3. **Code Splitting** (동적 import)
4. **정적 생성 (SSG)** 활용

```tsx
// frontend/src/app/layout.tsx
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',  // FOIT 방지
  variable: '--font-inter',
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
```

#### 2.1.8 모바일 친화성 (반응형 디자인)

**왜 필요한가?**
- Google Mobile-First Indexing (모바일 우선 색인)
- 모바일 트래픽 > 데스크톱 트래픽
- 검색 랭킹 필수 요소

**구현 위치:** 모든 페이지 (TailwindCSS 반응형 클래스 사용)

**코드 예시:**
```tsx
<div className="
  grid
  grid-cols-1 md:grid-cols-2 lg:grid-cols-3
  gap-4 md:gap-6 lg:gap-8
  p-4 md:p-6 lg:p-8
">
  {/* 모바일: 1열, 태블릿: 2열, 데스크톱: 3열 */}
</div>
```

**viewport 메타 태그 (필수):**
```tsx
// Next.js는 자동으로 추가하지만, 확인 필요
<meta name="viewport" content="width=device-width, initial-scale=1" />
```

#### 2.1.9 HTTPS 적용

**왜 필요한가?**
- Google 검색 랭킹 필수 요소
- 사용자 신뢰도 향상
- 브라우저 경고 방지

**현재 상태:** ✅ 적용 완료
- Nginx TLS 1.2/1.3
- cert-manager Let's Encrypt 자동 갱신
- HSTS 헤더 (Strict-Transport-Security)

#### 2.1.10 Canonical URL

**왜 필요한가?**
- 중복 콘텐츠 페널티 방지
- 검색 엔진에게 "정식 URL" 알림
- 파라미터가 다른 동일 페이지 통합

**구현 위치:** 각 페이지 메타데이터

**코드 예시:**
```tsx
// frontend/src/app/(public)/donations/page.tsx
export const metadata: Metadata = {
  title: '기부하기',
  alternates: {
    canonical: 'https://bodam.example/donations',
  },
};
```

---

### 2.2 권장 항목 (Nice to Have)

#### 2.2.1 Open Graph 이미지

**왜 필요한가?**
- 카카오톡, 페이스북 공유 시 썸네일 자동 표시
- SNS 유입 트래픽 증가

**구현 방법:**
```tsx
// frontend/src/app/opengraph-image.tsx (Next.js 자동 생성)
import { ImageResponse } from 'next/og';

export const runtime = 'edge';

export const alt = '보담 - 소방관 기부 플랫폼';
export const size = {
  width: 1200,
  height: 630,
};
export const contentType = 'image/png';

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 128,
          background: 'linear-gradient(to bottom, #ff4444, #ff6666)',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
        }}
      >
        보담 🚒
      </div>
    ),
    {
      ...size,
    }
  );
}
```

#### 2.2.2 Twitter Card

**구현 방법:** 메타데이터에 포함 (2.1.1 참고)

#### 2.2.3 빵부스러기 내비게이션 (Breadcrumb)

**왜 필요한가?**
- Google 검색 결과에 경로 표시 (Home > 기부하기 > 소방서 선택)
- 사용자 경험 향상
- 내부 링크 구조 강화

**코드 예시:**
```tsx
// frontend/src/components/Breadcrumb.tsx
export function Breadcrumb({ items }: { items: { label: string; href: string }[] }) {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.label,
      item: `https://bodam.example${item.href}`,
    })),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <nav aria-label="Breadcrumb">
        <ol className="flex gap-2 text-sm">
          {items.map((item, index) => (
            <li key={item.href}>
              {index > 0 && <span className="mr-2">/</span>}
              <a href={item.href}>{item.label}</a>
            </li>
          ))}
        </ol>
      </nav>
    </>
  );
}

// 사용 예시
<Breadcrumb
  items={[
    { label: '홈', href: '/' },
    { label: '기부하기', href: '/donations' },
    { label: '서울 중부소방서', href: '/fire-station-detail/1' },
  ]}
/>
```

#### 2.2.4 내부 링크 구조

**왜 필요한가?**
- Google PageRank 분산
- 크롤러가 깊은 페이지까지 수집
- 사용자 체류 시간 증가

**구현 방법:**
- 푸터에 주요 페이지 링크
- 관련 콘텐츠 추천 (소방서 상세 → 주변 소방서)
- 사이드바 인기 콘텐츠

#### 2.2.5 404 페이지 최적화

**왜 필요한가?**
- 사용자 이탈 방지
- 대체 콘텐츠 제공

**코드 예시:**
```tsx
// frontend/src/app/not-found.tsx (현재 존재)
export default function NotFound() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-6xl font-bold">404</h1>
      <p className="text-xl mt-4">페이지를 찾을 수 없습니다</p>

      <div className="mt-8">
        <Link href="/" className="text-blue-600 hover:underline">
          홈으로 돌아가기
        </Link>
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-semibold">추천 페이지</h2>
        <ul className="mt-4 space-y-2">
          <li><Link href="/donations">기부하기</Link></li>
          <li><Link href="/regions">지역별 소방서</Link></li>
          <li><Link href="/donation-ranking">기부 랭킹</Link></li>
        </ul>
      </div>
    </main>
  );
}
```

---

### 2.3 SEO 체크리스트 요약표

| 항목 | 우선순위 | 현재 상태 | 구현 위치 |
|------|---------|---------|----------|
| 메타 태그 (title, description) | 🔴 필수 | ⚠️ 부분 적용 | `app/layout.tsx`, 각 페이지 |
| Open Graph, Twitter Card | 🔴 필수 | ❌ 미적용 | `app/layout.tsx` metadata |
| robots.txt | 🔴 필수 | ❌ 미적용 | `public/robots.txt` |
| sitemap.xml | 🔴 필수 | ❌ 미적용 | `app/sitemap.ts` |
| JSON-LD Schema | 🔴 필수 | ❌ 미적용 | 각 페이지 컴포넌트 |
| 시맨틱 HTML | 🔴 필수 | ⚠️ 확인 필요 | 모든 페이지 |
| 이미지 alt | 🔴 필수 | ⚠️ 확인 필요 | 모든 `<Image>` |
| Core Web Vitals | 🔴 필수 | ⚠️ 측정 필요 | Lighthouse CI (CI/CD) |
| 모바일 친화성 | 🔴 필수 | ✅ TailwindCSS | 모든 페이지 |
| HTTPS | 🔴 필수 | ✅ 적용 완료 | Nginx TLS |
| Canonical URL | 🔴 필수 | ❌ 미적용 | 각 페이지 metadata |
| OG 이미지 생성 | 🟡 권장 | ❌ 미적용 | `app/opengraph-image.tsx` |
| Breadcrumb | 🟡 권장 | ❌ 미적용 | 컴포넌트 신규 생성 |
| 내부 링크 구조 | 🟡 권장 | ⚠️ 확인 필요 | Footer, Sidebar |
| 404 페이지 최적화 | 🟡 권장 | ✅ 적용 완료 | `app/not-found.tsx` |

---

## 3. 추가 성능 향상 방안

### 3.1 백엔드 성능 향상

#### 3.1.1 DB 쿼리 최적화 (N+1 문제, 인덱스)

**기대 효과:** 쿼리 응답 시간 50-90% 감소
**구현 난이도:** 중

**문제점:**
- N+1 쿼리: 부모 데이터 1개 + 자식 데이터 N개 조회 시 N+1번 쿼리 발생
- 인덱스 누락: WHERE, JOIN, ORDER BY 컬럼에 인덱스 없음

**해결 방법:**

**1) SQLAlchemy `joinedload` / `selectinload` 사용:**
```python
# 잘못된 예 (N+1 문제)
donations = await session.execute(select(Donation))
for donation in donations.scalars():
    print(donation.user.name)  # 각 donation마다 user 조회 (N번)

# 올바른 예 (Eager Loading)
from sqlalchemy.orm import joinedload

donations = await session.execute(
    select(Donation).options(joinedload(Donation.user))
)
for donation in donations.scalars():
    print(donation.user.name)  # user는 이미 로드됨
```

**2) 인덱스 추가:**
```python
# backend/src/models/donation.py
class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # 인덱스 추가
    fire_station_id = Column(Integer, ForeignKey("fire_stations.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # ORDER BY용
    status = Column(String, index=True)  # WHERE 조건용
```

**3) 복합 인덱스 (Composite Index):**
```python
# Alembic migration
def upgrade():
    op.create_index(
        'idx_donations_status_created',
        'donations',
        ['status', 'created_at'],  # 복합 인덱스
    )
```

**측정 방법:**
```python
# backend/src/database/slow_query.py 활용
from src.database.slow_query import log_slow_queries

# 느린 쿼리 로그 (500ms 이상)
async with log_slow_queries(threshold_ms=500):
    donations = await session.execute(select(Donation))
```

#### 3.1.2 Redis 캐싱 전략 강화

**기대 효과:** API 응답 시간 80-95% 감소 (캐시 히트 시)
**구현 난이도:** 중

**현재 상태:**
- Semantic Cache (Llama AI 쿼리): TTL 5분
- Celery 결과 캐시: Redis 사용

**추가 적용 대상:**
1. **소방서 목록** (거의 변경되지 않음)
2. **기부 랭킹** (1분마다 갱신)
3. **통계 데이터** (5분마다 갱신)

**구현 방법:**

**1) FastAPI Response 캐싱:**
```python
# backend/src/api/stations.py
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/api/fire-stations")
@cache(expire=3600)  # 1시간 캐시
async def get_fire_stations(
    region: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    # DB 조회
    stmt = select(FireStation)
    if region:
        stmt = stmt.where(FireStation.region == region)
    result = await session.execute(stmt)
    return result.scalars().all()
```

**2) Redis 초기화:**
```python
# backend/src/main.py
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost:6379", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

**3) 캐시 무효화 (Cache Invalidation):**
```python
# 소방서 정보 수정 시 캐시 삭제
from fastapi_cache import FastAPICache

@router.put("/api/fire-stations/{id}")
async def update_fire_station(id: int, data: FireStationUpdate):
    # 업데이트 로직
    await session.commit()

    # 캐시 삭제
    await FastAPICache.clear(namespace="get_fire_stations")
```

#### 3.1.3 DB Connection Pool 튜닝

**기대 효과:** 동시 접속자 처리 능력 20-40% 향상
**구현 난이도:** 하

**현재 설정:**
```python
pool_size=10
max_overflow=20
```

**튜닝 방법:**

**1) Gunicorn worker 수와 연동:**
```bash
# Gunicorn workers: 4
# DB pool_size = workers * 2 = 8
# max_overflow = workers * 4 = 16

# .env
DB_POOL_SIZE=8
DB_MAX_OVERFLOW=16
```

**2) HPA와 연동:**
```python
# Pod가 3개일 때:
# - 총 pool_size: 8 * 3 = 24
# - 총 max_overflow: 16 * 3 = 48
# - 최대 연결 수: 24 + 48 = 72 < PostgreSQL max_connections (100)
```

**3) Pool 모니터링:**
```python
# backend/src/database/pool_metrics.py (이미 존재)
from prometheus_client import Gauge

db_pool_size = Gauge('db_connection_pool_size', 'DB connection pool size')
db_pool_in_use = Gauge('db_connection_pool_in_use', 'DB connections in use')
db_pool_available = Gauge('db_connection_pool_available', 'Available DB connections')

# Prometheus로 확인
# db_connection_pool_in_use / db_connection_pool_size > 0.8 → pool_size 증가 필요
```

#### 3.1.4 Gunicorn Worker 최적화

**기대 효과:** 처리량 (Throughput) 30-50% 향상
**구현 난이도:** 하

**현재 상태:**
- Worker 수: 미확인 (Gunicorn 설정 파일 없음)
- Worker class: 미확인

**권장 설정:**

**1) Worker 수 공식:**
```bash
# CPU 코어 수 기반
workers = (2 * CPU_CORES) + 1

# DigitalOcean DOKS (2 vCPU 가정)
workers = (2 * 2) + 1 = 5
```

**2) Uvicorn Worker 사용 (비동기 지원):**
```bash
# backend/gunicorn.conf.py (신규 생성)
import multiprocessing

bind = "0.0.0.0:8080"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Timeouts
timeout = 30
graceful_timeout = 30

# Preload app (메모리 절약)
preload_app = True
```

**3) Dockerfile 수정:**
```dockerfile
# backend/Dockerfile
CMD ["gunicorn", "src.main:app", "-c", "gunicorn.conf.py"]
```

#### 3.1.5 FastAPI Response 캐싱

**기대 효과:** 정적 데이터 응답 시간 90% 감소
**구현 난이도:** 하

**(3.1.2 Redis 캐싱과 동일)**

#### 3.1.6 비동기 작업 최적화 (Celery)

**기대 효과:** 백그라운드 작업 처리 시간 20-40% 감소
**구현 난이도:** 중

**개선 방법:**

**1) Celery Worker Concurrency 증가:**
```bash
# infra/k8s/celery/celery-worker-deployment.yaml
command: ["celery", "-A", "src.workers.celery_app", "worker", "--concurrency=4", "--loglevel=info"]

# CPU 코어 수만큼 설정 (기본값: 1)
```

**2) Task 우선순위 설정:**
```python
# backend/src/workers/tasks.py
from celery import Task

@app.task(priority=0)  # 높은 우선순위 (0-9, 낮을수록 우선)
def send_email(to: str, subject: str):
    pass

@app.task(priority=5)  # 낮은 우선순위
def crawl_news():
    pass
```

**3) Batch 작업 최적화:**
```python
# 잘못된 예 (1000개 이메일 전송)
for user in users:
    send_email.delay(user.email)  # 1000번 Task 생성

# 올바른 예 (100개씩 묶음)
from celery import group

tasks = [send_email.s(user.email) for user in users]
job = group(tasks)
job.apply_async()
```

---

### 3.2 프론트엔드 성능 향상

#### 3.2.1 Next.js Image 최적화

**기대 효과:** 이미지 로딩 시간 50-70% 감소, LCP 개선
**구현 난이도:** 하

**현재 상태:**
- `next.config.js`에 `remotePatterns` 설정됨
- 일부 페이지에서 `<Image>` 사용

**개선 방법:**

**1) 모든 `<img>` 태그를 `<Image>`로 변경:**
```tsx
// 잘못된 예
<img src="/hero.jpg" />

// 올바른 예
import Image from 'next/image';

<Image
  src="/hero.jpg"
  width={1200}
  height={600}
  alt="소방관 기부 플랫폼"
  priority  // LCP 이미지는 priority 설정
  placeholder="blur"  // 블러 효과
  blurDataURL="data:image/..."
/>
```

**2) 이미지 포맷 최적화 (WebP, AVIF):**
```tsx
// Next.js 자동 변환 (next.config.js)
const nextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'],  // AVIF 우선, WebP fallback
  },
};
```

**3) Lazy Loading (스크롤 시 로드):**
```tsx
<Image
  src="/thumbnail.jpg"
  width={300}
  height={200}
  alt="썸네일"
  loading="lazy"  // 뷰포트에 들어올 때 로드
/>
```

#### 3.2.2 Code Splitting & Lazy Loading

**기대 효과:** 초기 번들 크기 30-50% 감소, FCP 개선
**구현 난이도:** 중

**구현 방법:**

**1) 동적 import (라우트 기반):**
```tsx
// frontend/src/app/(public)/donations/page.tsx
import dynamic from 'next/dynamic';

// 무거운 컴포넌트를 동적 로드
const DonationForm = dynamic(() => import('@/components/DonationForm'), {
  loading: () => <p>로딩 중...</p>,
  ssr: false,  // 클라이언트에서만 렌더링
});

export default function DonationsPage() {
  return (
    <main>
      <h1>기부하기</h1>
      <DonationForm />
    </main>
  );
}
```

**2) 조건부 import (모달, 차트):**
```tsx
// 모달을 클릭 시에만 로드
const [showModal, setShowModal] = useState(false);

const Modal = dynamic(() => import('@/components/Modal'));

return (
  <>
    <button onClick={() => setShowModal(true)}>모달 열기</button>
    {showModal && <Modal />}
  </>
);
```

**3) 라이브러리 최적화:**
```tsx
// 잘못된 예 (전체 lodash 로드)
import _ from 'lodash';

// 올바른 예 (필요한 함수만)
import debounce from 'lodash/debounce';
```

#### 3.2.3 Static Generation vs Server-Side Rendering

**기대 효과:** TTFB (Time to First Byte) 70-90% 감소
**구현 난이도:** 중

**전략:**
- **정적 페이지 (SSG)**: 홈, 소방서 목록, 뉴스 (빌드 시 생성)
- **동적 페이지 (SSR)**: 마이페이지, 기부 내역 (요청 시 생성)
- **클라이언트 렌더링 (CSR)**: 실시간 대시보드, 채팅

**구현 방법:**

**1) SSG (Static Site Generation):**
```tsx
// frontend/src/app/(public)/fire-station-detail/[id]/page.tsx
export async function generateStaticParams() {
  // 빌드 시 모든 소방서 ID를 미리 생성
  const stations = await fetch('https://api.bodam.example/api/fire-stations').then(res => res.json());

  return stations.map((station) => ({
    id: String(station.id),
  }));
}

export default async function FireStationPage({ params }: { params: { id: string } }) {
  // 빌드 시 데이터 fetch (런타임 아님)
  const station = await fetch(`https://api.bodam.example/api/fire-stations/${params.id}`).then(res => res.json());

  return <div>{station.name}</div>;
}
```

**2) ISR (Incremental Static Regeneration):**
```tsx
// 60초마다 재생성
export const revalidate = 60;

export default async function NewsPage() {
  const news = await fetch('https://api.bodam.example/api/news').then(res => res.json());

  return <div>{news.map(...)}</div>;
}
```

**3) SSR (Server-Side Rendering):**
```tsx
// 캐시 안 함 (매 요청마다 재생성)
export const dynamic = 'force-dynamic';

export default async function MyPage() {
  const user = await getCurrentUser();  // 쿠키 기반 인증

  return <div>{user.name}</div>;
}
```

#### 3.2.4 Prefetching & Preloading

**기대 효과:** 페이지 전환 속도 50-80% 향상
**구현 난이도:** 하

**구현 방법:**

**1) Next.js Link 자동 prefetch:**
```tsx
// Next.js는 viewport에 들어온 <Link>를 자동으로 prefetch
<Link href="/donations" prefetch={true}>
  기부하기
</Link>

// prefetch 비활성화 (외부 링크, 인증 페이지 등)
<Link href="/admin" prefetch={false}>
  관리자
</Link>
```

**2) 리소스 preload:**
```tsx
// frontend/src/app/layout.tsx
<head>
  {/* 주요 폰트 preload */}
  <link
    rel="preload"
    href="/fonts/inter.woff2"
    as="font"
    type="font/woff2"
    crossOrigin="anonymous"
  />

  {/* 주요 이미지 preload */}
  <link
    rel="preload"
    href="/hero.jpg"
    as="image"
  />
</head>
```

**3) DNS prefetch (외부 도메인):**
```tsx
<head>
  {/* 외부 API 도메인 DNS 조회 미리 수행 */}
  <link rel="dns-prefetch" href="https://api.bodam.example" />
  <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
</head>
```

#### 3.2.5 Font 최적화 (`font-display: swap`)

**기대 효과:** FOIT (Flash of Invisible Text) 방지, CLS 개선
**구현 난이도:** 하

**현재 상태:**
```tsx
// frontend/src/app/layout.tsx
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Pacifico&display=swap"
  rel="stylesheet"
/>
```
✅ `display=swap` 이미 적용됨

**추가 최적화:**

**1) 자체 호스팅 (Google Fonts 대신):**
```tsx
// frontend/src/app/layout.tsx
import localFont from 'next/font/local';

const inter = localFont({
  src: [
    {
      path: '../fonts/inter-regular.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../fonts/inter-bold.woff2',
      weight: '700',
      style: 'normal',
    },
  ],
  display: 'swap',
  variable: '--font-inter',
});

export default function RootLayout({ children }) {
  return (
    <html lang="ko" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
```

**2) 사용하지 않는 폰트 weight 제거:**
```tsx
// 잘못된 예 (9개 weight 모두 로드)
family=Inter:wght@300;400;500;600;700;800;900

// 올바른 예 (필요한 것만)
family=Inter:wght@400;700
```

#### 3.2.6 Third-party 스크립트 최적화

**기대 효과:** TBT (Total Blocking Time) 30-50% 감소
**구현 난이도:** 하

**현재 상태:**
```tsx
// frontend/src/app/layout.tsx
<head>
  <link
    rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
  />
  <link
    href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css"
    rel="stylesheet"
  />
</head>
```

**개선 방법:**

**1) Next.js Script 컴포넌트 사용:**
```tsx
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        {children}

        {/* Google Analytics (페이지 로드 후 실행) */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"
          strategy="afterInteractive"
        />

        {/* 광고 스크립트 (유휴 시간에 실행) */}
        <Script
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"
          strategy="lazyOnload"
        />
      </body>
    </html>
  );
}
```

**2) Icon 라이브러리 자체 호스팅:**
```bash
# Font Awesome, Remix Icon을 npm으로 설치
npm install @fortawesome/fontawesome-free

# public/fonts/ 디렉토리에 폰트 파일 복사
cp -r node_modules/@fortawesome/fontawesome-free/webfonts public/fonts/

# CSS 직접 import
import '@fortawesome/fontawesome-free/css/all.min.css';
```

---

### 3.3 인프라 성능 향상

#### 3.3.1 CDN 활용 강화 (Cloudflare)

**기대 효과:** 정적 파일 로딩 속도 40-60% 향상, 글로벌 TTFB 감소
**구현 난이도:** 중

**현재 상태:**
- Vercel CDN: 프론트엔드 (자동 적용)
- DigitalOcean Nginx: 백엔드 정적 파일

**추가 적용:**

**1) Cloudflare Free Tier 활용:**
- DNS 관리 + CDN (무료)
- DDoS 방어 (무료)
- Auto Minify (HTML, CSS, JS)

**설정 방법:**
1. Cloudflare에서 도메인 추가
2. DNS 레코드 설정:
   - `api.bodam.example` → DigitalOcean Load Balancer IP
   - `app.bodam.example` → Vercel CNAME
3. Page Rules 설정:
   - `/api/*`: Bypass cache (동적 콘텐츠)
   - `/static/*`: Cache Everything (1년)

#### 3.3.2 Brotli 압축 (gzip 대신)

**기대 효과:** 압축률 15-25% 개선 (gzip 대비)
**구현 난이도:** 하

**현재 상태:**
- Nginx gzip 압축 레벨 6

**개선 방법:**

**1) Nginx Brotli 모듈 활성화:**
```nginx
# infra/k8s/nginx/nginx-configmap.yaml
http {
    # Brotli 압축 (gzip보다 우선)
    brotli on;
    brotli_comp_level 6;
    brotli_types text/plain text/css text/xml text/javascript
                 application/json application/javascript application/xml+rss;

    # gzip fallback (구형 브라우저)
    gzip on;
    gzip_comp_level 6;
}
```

**2) Dockerfile에 Brotli 모듈 포함:**
```dockerfile
# infra/k8s/nginx/Dockerfile
FROM nginx:1.24-alpine

RUN apk add --no-cache nginx-mod-http-brotli

COPY nginx.conf /etc/nginx/nginx.conf
```

#### 3.3.3 HTTP/2 Server Push

**기대 효과:** 초기 페이지 로딩 10-20% 단축
**구현 난이도:** 중

**주의:** HTTP/2 Server Push는 2022년 Chrome에서 deprecated되었으므로, **Preload Link 헤더** 사용 권장

**구현 방법:**

**1) Nginx에서 Preload 헤더 추가:**
```nginx
# infra/k8s/nginx/nginx-configmap.yaml
location / {
    root /usr/share/nginx/html;

    # Preload 힌트 (브라우저가 우선순위 결정)
    add_header Link "</styles/main.css>; rel=preload; as=style";
    add_header Link "</scripts/main.js>; rel=preload; as=script";
    add_header Link "</fonts/inter.woff2>; rel=preload; as=font; crossorigin";
}
```

**2) Next.js에서 자동 처리 (기본 활성화됨):**
```tsx
// Next.js는 자동으로 주요 리소스에 preload 추가
// next.config.js에서 비활성화 가능 (비권장)
const nextConfig = {
  experimental: {
    optimizeCss: true,  // CSS preload 최적화
  },
};
```

#### 3.3.4 DNS Prefetch

**기대 효과:** 외부 도메인 연결 시간 50-100ms 단축
**구현 난이도:** 하

**구현 방법:**
```tsx
// frontend/src/app/layout.tsx
<head>
  <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
  <link rel="dns-prefetch" href="https://cdnjs.cloudflare.com" />
  <link rel="dns-prefetch" href="https://api.bodam.example" />
</head>
```

#### 3.3.5 Keep-Alive 최적화

**기대 효과:** HTTP 연결 재사용으로 요청 시간 20-30% 단축
**구현 난이도:** 하

**현재 상태:**
```nginx
# infra/k8s/nginx/nginx-configmap.yaml
keepalive_timeout 65;

upstream kong_upstream {
    server kong-gateway.default.svc.cluster.local:8000;
    keepalive 32;
}
```

**개선 방법:**

**1) Keep-Alive 타임아웃 증가:**
```nginx
http {
    keepalive_timeout 120;  # 65초 → 120초
    keepalive_requests 1000;  # 연결당 최대 요청 수
}
```

**2) 백엔드 httpx Keep-Alive 설정:**
```python
# backend/src/integrations/http_client.py (이미 적용됨)
httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20,  # Keep-Alive 연결 수
        keepalive_expiry=60.0,  # 60초 유지
    ),
)
```

---

### 3.4 성능 향상 우선순위 요약표

| 항목 | 기대 효과 | 구현 난이도 | 우선순위 | 비고 |
|------|---------|-----------|---------|------|
| **백엔드** |
| DB 쿼리 최적화 (N+1, 인덱스) | 50-90% ⬆️ | 중 | 🔴 높음 | 즉시 적용 권장 |
| Redis 캐싱 강화 | 80-95% ⬆️ | 중 | 🔴 높음 | 정적 데이터 우선 |
| DB Pool 튜닝 | 20-40% ⬆️ | 하 | 🟡 중간 | HPA와 연동 |
| Gunicorn Worker 최적화 | 30-50% ⬆️ | 하 | 🔴 높음 | gunicorn.conf.py 생성 |
| Celery 최적화 | 20-40% ⬆️ | 중 | 🟢 낮음 | Concurrency 증가 |
| **프론트엔드** |
| Next.js Image 최적화 | 50-70% ⬆️ | 하 | 🔴 높음 | 모든 `<img>` 변환 |
| Code Splitting | 30-50% ⬆️ | 중 | 🔴 높음 | 무거운 컴포넌트 우선 |
| SSG/ISR 적용 | 70-90% ⬆️ | 중 | 🔴 높음 | 정적 페이지부터 |
| Prefetching | 50-80% ⬆️ | 하 | 🟡 중간 | Link prefetch 활성화 |
| Font 최적화 | 10-20% ⬆️ | 하 | 🟡 중간 | 이미 적용 (display=swap) |
| Third-party 스크립트 | 30-50% ⬆️ | 하 | 🟡 중간 | Script 컴포넌트 사용 |
| **인프라** |
| Cloudflare CDN | 40-60% ⬆️ | 중 | 🟡 중간 | Free Tier 활용 |
| Brotli 압축 | 15-25% ⬆️ | 하 | 🟡 중간 | Nginx 모듈 추가 |
| DNS Prefetch | 50-100ms ⬇️ | 하 | 🟢 낮음 | `<link rel="dns-prefetch">` |
| Keep-Alive 최적화 | 20-30% ⬆️ | 하 | 🟢 낮음 | 이미 일부 적용 |

**우선순위 기준:**
- 🔴 높음: 투자 대비 효과가 크고 구현 난이도가 낮음
- 🟡 중간: 효과는 크지만 구현 난이도가 중간 이상
- 🟢 낮음: 효과가 제한적이거나 이미 부분 적용됨

---

## 4. 성능 측정 도구

### 4.1 백엔드 측정

**1) Prometheus + Grafana (이미 적용):**
- HTTP 요청 시간 (p50, p95, p99)
- DB 연결 풀 사용률
- Celery 작업 처리 시간

**2) K6 부하 테스트 (이미 적용):**
```bash
# 200 VU (동시 사용자) 테스트
K6_SCENARIO=target BASE_URL=http://backend:8000 k6 run --out statsd specs/004-hybrid-observability-stack/contracts/k6-scenarios.js
```

**3) DB 쿼리 프로파일링:**
```python
# backend/src/database/slow_query.py
from src.database.slow_query import log_slow_queries

async with log_slow_queries(threshold_ms=500):
    # 500ms 이상 걸리는 쿼리 자동 로그
    result = await session.execute(stmt)
```

### 4.2 프론트엔드 측정

**1) Lighthouse CI (이미 적용):**
```yaml
# .github/workflows/frontend-ci-cd.yml
- name: Lighthouse CI 실행
  uses: treosh/lighthouse-ci-action@v10
  with:
    urls: |
      ${{ steps.deploy.outputs.production_url }}
```

**2) Chrome DevTools:**
- Performance 탭: FCP, LCP, TBT, CLS 측정
- Network 탭: 리소스 크기, 로딩 시간

**3) Vercel Analytics (무료):**
```tsx
// frontend/src/app/layout.tsx
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        {children}
        <Analytics />  {/* 실제 사용자 Core Web Vitals 수집 */}
      </body>
    </html>
  );
}
```

---

## 5. 다음 단계 (Action Items)

### 5.1 즉시 실행 (1-2일)

- [ ] SEO: robots.txt, sitemap.xml 생성
- [ ] SEO: 메타 태그 (OG, Twitter Card) 추가
- [ ] 백엔드: Gunicorn 설정 파일 생성 (worker 수 최적화)
- [ ] 프론트엔드: `<img>` → `<Image>` 변환 (주요 페이지)
- [ ] 프론트엔드: Vercel Analytics 적용

### 5.2 단기 실행 (1주일)

- [ ] SEO: JSON-LD Schema 추가 (홈, 소방서 상세)
- [ ] 백엔드: DB 쿼리 N+1 문제 분석 및 수정
- [ ] 백엔드: Redis 캐싱 (소방서 목록, 랭킹)
- [ ] 프론트엔드: Code Splitting (무거운 컴포넌트)
- [ ] 프론트엔드: SSG/ISR 적용 (정적 페이지)

### 5.3 중기 실행 (1개월)

- [ ] SEO: Breadcrumb 컴포넌트 구현
- [ ] 백엔드: Celery Worker Concurrency 증가
- [ ] 인프라: Cloudflare CDN 도입
- [ ] 인프라: Nginx Brotli 압축 적용
- [ ] 성능: Lighthouse CI 통과 기준 설정 (LCP < 2.5s, CLS < 0.1)

---

## 6. 참고 자료

### 6.1 SEO
- [Google Search Central](https://developers.google.com/search)
- [Next.js Metadata API](https://nextjs.org/docs/app/api-reference/functions/generate-metadata)
- [Schema.org](https://schema.org/)

### 6.2 성능 최적화
- [Web.dev Core Web Vitals](https://web.dev/vitals/)
- [Next.js Performance](https://nextjs.org/docs/app/building-your-application/optimizing)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)

### 6.3 인프라
- [Nginx Performance Tuning](https://www.nginx.com/blog/tuning-nginx/)
- [PostgreSQL Connection Pooling](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [Vercel Analytics](https://vercel.com/docs/analytics)

---

**문서 작성일:** 2025-10-18
**작성자:** Claude (Anthropic)
**프로젝트:** BoDam (보담) - 소방관 기부 플랫폼
