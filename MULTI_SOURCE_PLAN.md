# 멀티 소스 스크래핑 전략

## 1차 소스: X(트위터) 한국 공식 계정 ⭐ 최우선
- **장점**: 실시간, 빠른 업데이트, 모든 픽업 포함, **한국어 지원**
- **계정**:
  - **@honkaisr_kr** (붕괴: 스타레일 한국 공식) 🇰🇷
  - **@ZZZ_KO** (젠레스 존 제로 한국 공식) 🇰🇷
  - @ZZZ_EN (젠레스 존 제로 글로벌) - 보조
  - @HonkaiStarRail (붕괴: 스타레일 글로벌) - 보조

## 2차 소스: HoYoLAB
- **장점**: 공식 한국어, 정확한 날짜 정보
- **용도**: 트위터 정보 검증 및 보완

## 3차 소스: 네이버 게임 라운지 (이미 구현됨)
- **장점**: 한국 커뮤니티 정보
- **용도**: 국내 일정 확인

## 구현 방안

### ❌ 시도했으나 실패한 방법들
1. **RSS 피드 (Nitter)**: Nitter 인스턴스들이 차단되어 작동 안 함
2. **Selenium 웹 스크래핑**: 로그인 없이는 제한적 접근만 가능
3. **Twitter API v2**: 월 $100+ 비용 발생

### ✅ 현실적인 해결책: **HoYoLAB + 수동 보완**

X(트위터)는 2023년 이후 외부 접근을 대폭 제한했습니다.
무료로 안정적으로 스크래핑하기는 거의 불가능합니다.

**추천 방안:**
1. **HoYoLAB 스크래퍼 개선** (이미 완료) ⭐
   - 날짜 파싱 강화
   - 키워드 감지 개선
   - 12시간마다 자동 실행
   
2. **네이버 게임 라운지** (이미 구현됨) ⭐
   - 한국 커뮤니티 정보
   - Selenium으로 안정적 수집
   
3. **필요시 수동 추가 스크립트** ⭐
   - 누락 발견 시 빠르게 추가 가능
   - `scripts/add_missing_*.py` 활용

### X(트위터) 활용하려면
- **Twitter API Basic ($100/month)** 구독 필요
- 또는 수동으로 확인 후 스크립트로 추가

```python
# 예시 구현
import feedparser

# Nitter RSS 피드
feeds = [
    "https://nitter.net/ZZZ_EN/rss",
    "https://nitter.net/HonkaiStarRail/rss",
]

for feed_url in feeds:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        # 'banner', 'warp', 'channel' 키워드 감지
        if any(kw in entry.title.lower() for kw in ['banner', 'warp', 'channel']):
            # 날짜 파싱 및 저장
            ...
```

## 장점
1. **무료**
2. **API 키 불필요**
3. **안정적**
4. **실시간 업데이트**

