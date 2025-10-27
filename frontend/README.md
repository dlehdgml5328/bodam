
# 🚒 소방관 기부 플랫폼 (Next.js)

> **⚠️ 중요: 이 프로젝트는 Next.js로 구축되었습니다. React SPA로 변환하지 마세요!**

## 🛡️ 프로젝트 보호 규칙

**절대 금지 사항:**
- ❌ React SPA로 변환 금지
- ❌ Vite 변환 금지  
- ❌ CRA 변환 금지
- ❌ 자동 변환 시스템 적용 금지

**반드시 유지:**
- ✅ Next.js Pages Router 구조
- ✅ pages/ 폴더 구조
- ✅ next.config.js 설정
- ✅ Next.js 전용 기능들

## 🏗️ 프로젝트 구조

```
소방관-기부-플랫폼/
├── pages/                    # Next.js 페이지 (절대 변경 금지)
│   ├── _app.tsx             # Next.js 앱 설정
│   ├── _document.tsx        # Next.js 문서 설정
│   ├── index.tsx            # 홈페이지
│   ├── donations.tsx        # 기부하기
│   ├── regions.tsx          # 지역별 현황
│   ├── donation-ranking.tsx # 기부 랭킹
│   ├── regular-donation.tsx # 단체 기부
│   ├── mypage.tsx          # 마이페이지
│   └── payment/            # 결제 관련
├── components/              # 컴포넌트
├── styles/                 # 스타일
├── next.config.js          # Next.js 설정 (중요!)
└── package.json           # 의존성 관리
```

## 🚀 실행 방법

```bash
# 의존성 설치
npm install

# 개발 서버 시작
npm run dev

# 빌드
npm run build

# 프로덕션 시작
npm start
```

## 🔧 환경 변수

프론트엔드에서 FastAPI 백엔드 주소를 지정하려면 `.env.local` 파일에 다음 값을 설정하세요.

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

실제 배포 환경에서는 HTTPS가 적용된 API 엔드포인트로 변경해야 합니다.

## 📋 기술 스택

- **Framework:** Next.js 13.5.6 (Pages Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Payment:** Toss Payments
- **Icons:** Remix Icon

## 🔒 자동 변환 방지 설정

이 프로젝트는 다음과 같은 방법으로 자동 변환을 방지합니다:

1. **package.json** - 명확한 Next.js 식별자
2. **next.config.js** - 강화된 Next.js 설정
3. **프로젝트 구조** - Next.js 전용 폴더 구조
4. **환경 변수** - 프레임워크 타입 명시

## ⚡ 주요 기능

- 개인 기부하기
- 단체 기부 신청
- 지역별 소방서 현황
- 실시간 기부 랭킹
- 결제 시스템 (Toss Payments)
- 반응형 디자인

## 📞 지원

- 고객센터: 1588-1234
- 이메일: support@firefighter-donation.com

---

**🚨 다시 한번 강조: 이 프로젝트는 Next.js입니다. 절대 React SPA로 변환하지 마세요!**
# Frontend Deployment Test

## Vercel Auto-Deploy Test
Last updated: Mon Oct 27 11:51:25 KST 2025
