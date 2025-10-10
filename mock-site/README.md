# Mock Fire Station Site

실시간 소방 출동 현황 Mock 데이터 사이트 (크롤링 테스트용)

## 📋 개요

이 사이트는 **보담(BoDam)** 프로젝트의 크롤링 시스템 테스트를 위해 만들어진 Mock 사이트입니다.
30개의 가상 소방 출동 데이터를 10초마다 순환하며 표시합니다.

## 🚀 특징

- **30개 출동 데이터**: 전국 주요 소방서의 실제 출동 형식 데이터
- **10초 순환**: 자동으로 다음 데이터로 갱신 (배포 시 5분으로 변경 가능)
- **크롤링 친화적**: `data-*` 속성으로 구조화된 데이터 제공
- **GitHub Pages 배포**: 정적 사이트로 무료 호스팅

## 📂 디렉토리 구조

```
mock-site/
├── index.html           # 메인 페이지
├── data/
│   └── incidents.json   # 30개 출동 데이터
├── js/
│   └── update.js        # 10초 순환 로직
├── css/
│   └── style.css        # 스타일
└── README.md            # 이 파일
```

## 📊 데이터 형식

```json
{
  "id": "20241009001",
  "union": "11",
  "status": "A",
  "fireName": "서울강남소방서",
  "address": "서울 강남구 역삼동 테헤란로 123",
  "axisX": 127.0376,
  "axisY": 37.4979,
  "occurrenceTime": "14:32",
  "casualties": 0,
  "injured": 0,
  "damageAmount": 0,
  "progress": "화재진압"
}
```

### 상태 코드
- `A`: 출동 중
- `B`: 현장 도착
- `C`: 진압 완료
- `D`: 귀소

## 🤖 크롤링 포인트

백엔드에서 크롤링 시 다음 요소를 사용하세요:

```python
# BeautifulSoup 예시
soup = BeautifulSoup(html, 'html.parser')
incident_div = soup.find('div', {'class': 'incident'})

incident = {
    'id': incident_div.get('data-id'),
    'fireName': incident_div.find('h2', {'class': 'fire-name'}).text,
    'address': incident_div.find('p', {'class': 'address'}).text.strip(),
    'occurrenceTime': incident_div.find('p', {'class': 'time'}).text.replace('발생시간: ', ''),
    'axisY': float(incident_div.get('data-lat')),
    'axisX': float(incident_div.get('data-lng')),
    'progress': incident_div.find('p', {'class': 'progress'}).text.strip(),
}
```

## 🌐 GitHub Pages 배포

### 1. 레포지토리 생성

```bash
# 현재 디렉토리에서
git init
git add .
git commit -m "Initial mock site"
```

### 2. GitHub 레포 생성 및 푸시

```bash
gh repo create mock-fire-station-site --public --source=. --remote=origin
git push -u origin main
```

### 3. GitHub Pages 활성화

1. GitHub 레포 → Settings → Pages
2. Source: `main` branch 선택
3. Save 클릭
4. 배포 URL: `https://USERNAME.github.io/mock-fire-station-site/`

### 4. 환경 변수 설정

배포 후 Backend `.env`에 URL 추가:

```bash
MOCK_SITE_URL=https://USERNAME.github.io/mock-fire-station-site/
```

## 🔧 로컬 테스트

```bash
# Python HTTP 서버로 로컬 테스트
cd mock-site
python -m http.server 8000

# 브라우저에서 접속
open http://localhost:8000
```

## ⏱️ 갱신 주기 변경

**개발용 (10초)**:
```javascript
// js/update.js
const rotationInterval = 10000; // 10초
```

**프로덕션용 (5분)**:
```javascript
// js/update.js
const rotationInterval = 300000; // 5분
```

## 📝 데이터 추가/수정

`data/incidents.json` 파일을 편집하여 데이터를 추가하거나 수정할 수 있습니다.

```json
[
  {
    "id": "새로운ID",
    "union": "지역코드",
    "status": "A/B/C/D",
    ...
  }
]
```

## 🧪 Backend 크롤링 테스트

```python
# backend/src/tasks/crawler.py
import httpx
from bs4 import BeautifulSoup

MOCK_SITE_URL = "https://USERNAME.github.io/mock-fire-station-site/"

async def test_crawl():
    async with httpx.AsyncClient() as client:
        response = await client.get(MOCK_SITE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')

        incident = soup.find('div', {'class': 'incident'})
        print(f"ID: {incident.get('data-id')}")
        print(f"소방서: {incident.find('h2').text}")
        print(f"주소: {incident.find('p', {'class': 'address'}).text}")
```

## 📈 모니터링

- **개발자 콘솔**: 브라우저 콘솔에서 로그 확인
- **Network 탭**: `incidents.json` 로딩 확인
- **Elements 탭**: `.incident` 요소 구조 확인

## 🐛 트러블슈팅

### CORS 에러
GitHub Pages는 기본적으로 CORS를 허용합니다. 로컬 테스트 시에는 브라우저 CORS 확장 사용.

### 데이터 로딩 실패
1. `data/incidents.json` 경로 확인
2. JSON 형식 검증 (https://jsonlint.com/)
3. 네트워크 탭에서 404 에러 확인

### 순환 안 됨
1. 브라우저 콘솔에서 JavaScript 에러 확인
2. `js/update.js` 로드 확인
3. `rotateIncidents()` 함수 실행 확인

## 📄 라이선스

이 프로젝트는 개발 및 테스트 목적으로만 사용됩니다.

---

**작성일**: 2025-10-10
**프로젝트**: 보담(BoDam) - 소방대원 커피 기부 플랫폼
**용도**: Mock 크롤링 사이트
