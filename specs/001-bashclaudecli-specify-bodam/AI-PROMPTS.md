# AI 프롬프트 가이드 🤖

## 개요
보담 플랫폼에서 사용하는 AI 분석 시스템의 프롬프트 설계, 최적화 전략, 품질 관리 방안을 정의합니다.

## 🧠 AI 아키텍처

### Together AI Llama 3.3 70B 활용
```python
# AI 클라이언트 설정
from together import Together

class BodamAIClient:
    def __init__(self):
        self.client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
        self.max_tokens = 4096
        self.temperature = 0.1  # 일관성을 위한 낮은 온도
```

### 분석 파이프라인
1. **콘텐츠 수집**: 뉴스/유튜브/재난문자 크롤링
2. **전처리**: 텍스트 정제, 메타데이터 추출
3. **AI 분석**: 화재 관련성 판별, 신뢰도 점수 산출
4. **후처리**: 결과 검증, 알림 발송 결정

## 🔥 화재 사건 분석 프롬프트

### 1. 기본 관련성 판별
```python
FIRE_RELEVANCE_PROMPT = """
다음 뉴스 기사나 재난문자가 실제 화재 사건과 관련이 있는지 분석해주세요.

분석할 텍스트:
{content}

메타데이터:
- 발행일시: {timestamp}
- 출처: {source}
- 지역: {location}

분석 기준:
1. 실제 화재 사건 여부 (건물화재, 산불, 차량화재 등)
2. 허위 정보나 루머가 아닌 신뢰할 수 있는 정보
3. 과거 사건 회고나 교육 목적이 아닌 현재 진행형 사건
4. 한국 내 발생 사건 (해외 사건 제외)

응답 형식 (JSON):
{
  "is_fire_related": true/false,
  "confidence_score": 0.0-1.0,
  "fire_type": "building/wildfire/vehicle/industrial/other",
  "severity": "minor/moderate/major/critical",
  "location": {
    "region": "시/도",
    "district": "시/구/군",
    "coordinates": {"lat": 37.5665, "lng": 126.9780}
  },
  "timestamp_extracted": "2025-09-19T14:30:00+09:00",
  "casualties": {
    "injured": 0,
    "deaths": 0,
    "evacuated": 0
  },
  "response_units": ["소방서명1", "소방서명2"],
  "reasoning": "판단 근거를 한국어로 설명"
}
"""
```

### 2. 소방서 연관성 분석
```python
STATION_MAPPING_PROMPT = """
화재 사건 위치를 기반으로 대응하는 소방서를 식별해주세요.

사건 정보:
- 위치: {location_text}
- 좌표: {coordinates}
- 화재 규모: {severity}

소방서 데이터베이스:
{fire_stations_json}

분석 요청:
1. 사건 위치에서 가장 가까운 소방서 3곳 식별
2. 화재 규모에 따른 지원 소방서 예측
3. 교통 상황을 고려한 대응 우선순위

응답 형식 (JSON):
{
  "primary_station": {
    "id": "station_uuid",
    "name": "소방서명",
    "distance_km": 2.5,
    "estimated_response_time": "5분"
  },
  "supporting_stations": [
    {
      "id": "station_uuid",
      "name": "소방서명",
      "role": "backup/specialist/aerial",
      "distance_km": 4.2
    }
  ],
  "confidence": 0.95,
  "reasoning": "선정 근거"
}
"""
```

### 3. 심각도 평가
```python
SEVERITY_ASSESSMENT_PROMPT = """
화재 사건의 심각도를 평가하고 기부 알림 필요성을 판단해주세요.

사건 상세정보:
{incident_details}

평가 기준:
- Minor (경미): 작은 규모, 인명피해 없음, 빠른 진압
- Moderate (보통): 중간 규모, 경상자 발생 가능, 일반적 대응
- Major (심각): 대규모, 중상자/사망자 발생, 다수 소방서 출동
- Critical (위험): 초대형, 다수 사상자, 특수 장비 필요

기부 알림 기준:
- Moderate 이상: 기부자들에게 알림 발송
- Major 이상: 긴급 알림 + 추가 기부 독려
- Critical: 재난 상황 알림 + 특별 기부 캠페인

응답 형식 (JSON):
{
  "severity_level": "minor/moderate/major/critical",
  "notification_required": true/false,
  "notification_type": "standard/urgent/emergency",
  "estimated_cost": 50000000,
  "priority_needs": ["식음료", "의료용품", "임시숙소"],
  "campaign_suggestion": "특별 기부 캠페인 제안",
  "reasoning": "평가 근거"
}
"""
```

## 📰 뉴스 콘텐츠 분석

### 1. 뉴스 신뢰도 검증
```python
NEWS_CREDIBILITY_PROMPT = """
뉴스 기사의 신뢰도를 평가해주세요.

기사 정보:
- 제목: {title}
- 본문: {content}
- 출처: {source}
- 기자: {author}
- 발행시간: {published_at}

검증 기준:
1. 출처 신뢰도 (공신력 있는 언론사)
2. 내용 일관성 (제목과 본문 일치)
3. 팩트 체크 (구체적 정보 포함)
4. 편향성 검사 (객관적 서술)
5. 중복성 확인 (기존 보도와 비교)

응답 형식 (JSON):
{
  "credibility_score": 0.0-1.0,
  "source_reliability": "high/medium/low",
  "content_quality": "excellent/good/fair/poor",
  "bias_detected": true/false,
  "fact_check_status": "verified/unverified/disputed",
  "duplicate_content": true/false,
  "recommendation": "approve/review/reject",
  "reasoning": "평가 상세 설명"
}
"""
```

### 2. 키워드 추출 및 분류
```python
KEYWORD_EXTRACTION_PROMPT = """
화재 관련 뉴스에서 핵심 키워드를 추출하고 분류해주세요.

뉴스 내용:
{news_content}

추출 카테고리:
1. 위치 키워드: 주소, 건물명, 지역명
2. 화재 유형: 건물화재, 산불, 공장화재 등
3. 피해 규모: 인명피해, 재산피해
4. 대응 기관: 소방서, 경찰서, 병원
5. 시간 정보: 발생시간, 신고시간, 진압시간

응답 형식 (JSON):
{
  "location_keywords": ["강남구", "삼성동", "코엑스"],
  "fire_type_keywords": ["건물화재", "아파트"],
  "damage_keywords": ["부상자 3명", "재산피해 5억원"],
  "response_keywords": ["강남소방서", "삼성119안전센터"],
  "time_keywords": ["14시 30분 발생", "15시 진압"],
  "emergency_level": "urgent/normal/low",
  "action_keywords": ["대피", "교통통제", "화재조사"]
}
"""
```

## 🎬 유튜브 콘텐츠 분석

### 1. 영상 콘텐츠 분류
```python
YOUTUBE_ANALYSIS_PROMPT = """
유튜브 영상이 실제 화재 사건 보도인지 분석해주세요.

영상 정보:
- 제목: {title}
- 설명: {description}
- 채널: {channel}
- 업로드 시간: {upload_time}
- 조회수: {view_count}
- 댓글 수: {comment_count}

분류 기준:
1. 실제 사건 보도 vs 과거 사건 정리
2. 공식 언론사 vs 개인 유튜버
3. 1차 정보 vs 2차 편집 콘텐츠
4. 실시간 중계 vs 사후 분석

제외 대상:
- 게임/영화 콘텐츠
- 교육/안전 콘텐츠
- 허위/선정적 썸네일
- 광고/홍보 목적

응답 형식 (JSON):
{
  "content_type": "breaking_news/documentary/educational/entertainment/spam",
  "is_legitimate_news": true/false,
  "channel_credibility": "official_media/verified_creator/individual/suspicious",
  "content_freshness": "live/recent/archived/old",
  "relevance_score": 0.0-1.0,
  "red_flags": ["clickbait_title", "fake_thumbnail", "spam_description"],
  "recommendation": "include/flag_for_review/exclude",
  "reasoning": "분석 근거"
}
"""
```

### 2. 영상 썸네일 분석
```python
THUMBNAIL_ANALYSIS_PROMPT = """
유튜브 썸네일 이미지를 분석하여 내용의 신뢰성을 판단해주세요.

이미지 분석 요소:
1. 실제 화재 현장 사진 vs 합성/편집 이미지
2. 선정적 요소 (과도한 텍스트, 화살표, 놀란 표정)
3. 저해상도/픽셀화된 이미지
4. 시각적 일관성 (제목과 이미지 매칭)

신뢰도 지표:
- High: 뉴스 영상 스타일, 깔끔한 구성
- Medium: 개인 제작, 적당한 편집
- Low: 선정적 편집, 명확한 클릭베이트

응답 형식 (JSON):
{
  "thumbnail_quality": "professional/amateur/poor",
  "clickbait_elements": ["exaggerated_text", "arrows", "shocked_face"],
  "visual_credibility": "high/medium/low",
  "content_match": "title_matches/partial_match/misleading",
  "recommendation": "trust/caution/reject"
}
"""
```

## 📱 재난문자 분석

### 1. 재난문자 파싱
```python
EMERGENCY_ALERT_PROMPT = """
재난문자 내용을 파싱하여 화재 정보를 추출해주세요.

재난문자 원문:
{alert_message}

수신 정보:
- 수신 시간: {received_time}
- 발신 기관: {sender}
- 지역 코드: {area_code}

추출할 정보:
1. 화재 발생 위치 (상세 주소)
2. 화재 발생 시간
3. 화재 유형 및 규모
4. 대피 정보
5. 교통 통제 정보
6. 주의사항

응답 형식 (JSON):
{
  "alert_type": "fire_outbreak/evacuation_order/traffic_control/all_clear",
  "incident_location": {
    "address": "서울시 강남구 테헤란로 123",
    "landmark": "코엑스 인근",
    "coordinates": {"lat": 37.5665, "lng": 126.9780}
  },
  "incident_time": "2025-09-19T14:30:00+09:00",
  "fire_details": {
    "type": "building_fire",
    "building_type": "commercial",
    "floors_affected": "2-5층"
  },
  "public_safety": {
    "evacuation_zone": "반경 200m",
    "traffic_restrictions": ["테헤란로 양방향 통제"],
    "public_warning": "연기 흡입 주의"
  },
  "urgency_level": "immediate/high/moderate/low"
}
"""
```

### 2. 재난문자 진위 확인
```python
ALERT_VERIFICATION_PROMPT = """
재난문자의 진위성을 확인해주세요.

검증 대상:
- 발신 기관: {sender_agency}
- 문자 형식: {message_format}
- 시간 정보: {timestamp_info}
- 연락처/웹사이트: {contact_info}

검증 기준:
1. 공식 발신 기관 확인 (소방청, 지자체)
2. 메시지 형식 정합성
3. 연락처 정보 유효성
4. 중복 발신 패턴
5. 외부 소스 교차 검증

의심 신호:
- 비공식 발신자
- 이상한 문구/맞춤법
- 의심스러운 연락처
- 과도한 공포 조장

응답 형식 (JSON):
{
  "authenticity": "verified/suspected_fake/uncertain",
  "sender_legitimacy": "official_agency/verified_source/suspicious/fake",
  "format_compliance": true/false,
  "cross_verification": "confirmed/partial/none",
  "risk_level": "safe/caution/high_risk",
  "recommendation": "process/flag/block",
  "verification_notes": "검증 과정 상세 기록"
}
"""
```

## 🎯 AI 품질 관리

### 1. 응답 품질 검증
```python
class AIResponseValidator:
    def validate_fire_analysis(self, response: dict) -> bool:
        required_fields = [
            "is_fire_related", "confidence_score",
            "fire_type", "severity", "reasoning"
        ]

        # 필수 필드 존재 확인
        if not all(field in response for field in required_fields):
            return False

        # 신뢰도 점수 범위 확인 (0.0-1.0)
        if not 0.0 <= response["confidence_score"] <= 1.0:
            return False

        # 화재 유형 유효성 확인
        valid_types = ["building", "wildfire", "vehicle", "industrial", "other"]
        if response["fire_type"] not in valid_types:
            return False

        return True
```

### 2. 편향성 모니터링
```python
BIAS_DETECTION_PROMPT = """
AI 분석 결과에서 편향성을 검사해주세요.

분석 결과:
{ai_response}

편향성 검사 항목:
1. 지역 편향 (특정 지역 과대/과소 평가)
2. 출처 편향 (특정 언론사 선호/기피)
3. 시간 편향 (특정 시간대 과민/둔감 반응)
4. 규모 편향 (작은 사건 무시, 큰 사건 과대평가)

공정성 기준:
- 동일한 조건의 사건은 동일하게 평가
- 출처에 관계없이 내용 중심 판단
- 지역/시간에 관계없이 일관된 기준 적용

응답 형식 (JSON):
{
  "bias_detected": true/false,
  "bias_types": ["regional", "source", "temporal", "scale"],
  "severity": "minor/moderate/significant",
  "affected_decision": "classification/scoring/routing",
  "recommendation": "accept/flag/retrain"
}
"""
```

### 3. 성능 최적화
```python
# 프롬프트 성능 메트릭
class PromptMetrics:
    def __init__(self):
        self.accuracy_scores = []
        self.response_times = []
        self.token_usage = []

    def track_performance(self, prompt_version: str,
                         accuracy: float, latency: float, tokens: int):
        self.metrics[prompt_version] = {
            "accuracy": accuracy,
            "avg_latency": latency,
            "token_efficiency": tokens,
            "last_updated": datetime.now()
        }
```

## 🔄 프롬프트 버전 관리

### 1. 프롬프트 버저닝
```python
PROMPT_VERSIONS = {
    "fire_analysis_v3.2": {
        "template": FIRE_RELEVANCE_PROMPT,
        "accuracy": 0.94,
        "deployment_date": "2025-09-15",
        "changelog": "화재 유형 분류 개선"
    },
    "news_credibility_v2.1": {
        "template": NEWS_CREDIBILITY_PROMPT,
        "accuracy": 0.89,
        "deployment_date": "2025-09-10",
        "changelog": "편향성 검사 강화"
    }
}
```

### 2. A/B 테스트
```python
async def run_prompt_ab_test(content: str, version_a: str, version_b: str):
    # 트래픽을 50:50으로 분할하여 테스트
    if random.random() < 0.5:
        result = await analyze_with_prompt(content, version_a)
        log_experiment("A", version_a, result)
    else:
        result = await analyze_with_prompt(content, version_b)
        log_experiment("B", version_b, result)

    return result
```

## 🚨 AI 안전장치

### 1. 출력 필터링
```python
class AIOutputFilter:
    def filter_response(self, response: dict) -> dict:
        # 개인정보 마스킹
        if "personal_info" in response:
            response["personal_info"] = self.mask_pii(response["personal_info"])

        # 부적절한 내용 필터링
        if self.contains_inappropriate_content(response):
            response["content_warning"] = True

        return response
```

### 2. 폴백 메커니즘
```python
async def analyze_with_fallback(content: str) -> dict:
    try:
        # 주 AI 모델 시도
        result = await primary_ai_analysis(content)
        if validate_response(result):
            return result
    except Exception as e:
        logger.warning(f"Primary AI failed: {e}")

    try:
        # 보조 AI 모델 시도
        result = await secondary_ai_analysis(content)
        if validate_response(result):
            return result
    except Exception as e:
        logger.error(f"Secondary AI failed: {e}")

    # 기본 규칙 기반 분석
    return rule_based_analysis(content)
```

---

이 AI 프롬프트 가이드는 보담 플랫폼의 AI 분석 시스템의 정확성과 신뢰성을 보장하기 위한 종합적인 가이드입니다. 지속적인 개선과 최적화를 통해 더욱 정확한 화재 사건 분석을 제공합니다.