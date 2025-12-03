# Steam 발매예정 게임 스크래퍼 설정

## 환경 변수

### `MIN_WISHLIST_COUNT` (최소 찜 횟수)
- **기본값**: `5000`
- **설명**: 이 값보다 찜 횟수가 적은 게임은 필터링됩니다.
- **예시**:
  - `5000`: 찜 5,000회 이상인 게임만 수집
  - `10000`: 찜 10,000회 이상인 게임만 수집
  - `1000`: 찜 1,000회 이상인 게임만 수집
  - `0`: 필터링 없음 (모든 게임 수집)

### `ROLLING_MONTHS`
- **기본값**: `3`
- **설명**: 현재 기준 앞으로 몇 개월 간의 게임을 수집할지 설정

### `MAX_PAGES`
- **기본값**: `10`
- **설명**: Steam 검색 결과 페이지를 몇 페이지까지 탐색할지 설정

## 사용 예시

### 로컬에서 실행
```bash
# 찜 5천회 이상 게임만 수집
MIN_WISHLIST_COUNT=5000 python scripts/scrape_comingsoon.py

# 찜 1만회 이상 게임만 수집
MIN_WISHLIST_COUNT=10000 python scripts/scrape_comingsoon.py

# 필터링 없이 모든 게임 수집
MIN_WISHLIST_COUNT=0 python scripts/scrape_comingsoon.py
```

### GitHub Actions에서 설정
`.github/workflows/scrape_comingsoon.yml` 파일의 `env` 섹션에서 수정:

```yaml
env:
  MIN_WISHLIST_COUNT: '5000'  # 원하는 값으로 변경
```

## 찜 횟수 기준 가이드

- **5,000회 이상**: 중간 인기 게임 (추천 ⭐)
- **10,000회 이상**: 높은 인기 게임
- **20,000회 이상**: 매우 높은 인기 게임 (AAA급)
- **50,000회 이상**: 초대형 타이틀

## 주의사항

1. 찜 횟수 정보는 Steam Store 페이지에서 스크래핑하므로 API 호출이 증가합니다.
2. 찜 횟수를 가져올 수 없는 게임은 자동으로 필터링됩니다.
3. 너무 높은 기준을 설정하면 수집되는 게임이 매우 적어질 수 있습니다.

