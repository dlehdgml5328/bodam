# Vercel GitHub Secrets 설정 가이드

## 1. VERCEL_TOKEN 생성

1. https://vercel.com/account/tokens 접속
2. "Create Token" 버튼 클릭
3. Token 이름 입력 (예: "GitHub Actions")
4. Scope: Full Account 선택
5. Expiration: No Expiration 선택 (또는 원하는 기간)
6. "Create" 클릭
7. **생성된 토큰을 복사** (다시 볼 수 없으니 주의!)

## 2. VERCEL_ORG_ID 및 VERCEL_PROJECT_ID 확인

### 방법 1: Vercel 웹사이트에서 확인
1. https://vercel.com/dashboard 접속
2. 프로젝트 선택
3. Settings → General 탭
4. "Project ID" 복사 → 이것이 `VERCEL_PROJECT_ID`
5. Settings → General에서 아래로 스크롤
6. "Organization ID" 또는 "Team ID" 복사 → 이것이 `VERCEL_ORG_ID`

### 방법 2: 터미널에서 확인 (더 쉬움)
```bash
cd /home/donghee/bodam/frontend
npx vercel login
npx vercel link
```

위 명령어 실행 후 `.vercel/project.json` 파일이 생성됩니다:
```bash
cat .vercel/project.json
```

출력 예시:
```json
{
  "orgId": "team_XXXXXXXXXX",
  "projectId": "prj_XXXXXXXXXX"
}
```

## 3. GitHub Secrets에 추가

1. GitHub 저장소 페이지 이동
2. Settings → Secrets and variables → Actions
3. "New repository secret" 클릭
4. 다음 항목들을 하나씩 추가:

   - Name: `VERCEL_TOKEN`
     Value: [1단계에서 생성한 토큰]

   - Name: `VERCEL_ORG_ID`
     Value: [2단계에서 확인한 orgId]

   - Name: `VERCEL_PROJECT_ID`
     Value: [2단계에서 확인한 projectId]

## 4. 확인

모든 Secrets가 추가되면 다음 항목들이 보여야 합니다:
- ✅ VERCEL_TOKEN
- ✅ VERCEL_ORG_ID
- ✅ VERCEL_PROJECT_ID
- ✅ SLACK_WEBHOOK_URL (기존)
- ✅ DIGITALOCEAN_TOKEN (기존)
- ✅ DATABASE_URL (기존)
- 등등...

## 5. 테스트

Secrets 추가 후 frontend 코드를 수정하고 푸시하면 자동으로 Vercel 배포가 시작됩니다!

```bash
# 테스트용 커밋
cd /home/donghee/bodam
git add .
git commit -m "test: Trigger frontend CI/CD"
git push origin develop
```
