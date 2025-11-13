# 특별방송 크롤링 실패 원인 분석 및 수정

## 문제 상황

두 개의 특별방송 공지를 크롤링하지 못했습니다:

1. **명조 2.8 버전 프리뷰 특별 방송**
   - URL: https://game.naver.com/lounge/WutheringWaves/board/detail/6916931
   - 게시판: 네이버 게임 라운지 명조 공지사항

2. **젠레스 존 제로 2.4 버전 특별 방송 예고**
   - URL: https://www.hoyolab.com/article/42300532
   - 게시판: HoYoLAB 젠존제 공식 계정

## 원인 분석

### 1. 명조 특별방송 크롤링 실패 원인

**문제점:**
- 제목에 이모지(📣)가 포함되어 있어 키워드 매칭이 실패
- 제목: `📣『명조:워더링 웨이브』 2.8 버전 프리뷰 특별 방송`
- 기존 코드는 이모지를 고려하지 않고 직접 비교했음

**위치:** `scripts/scrape_lounge.py` - `parse_ww()` 함수

### 2. 젠존제 특별방송 크롤링 실패 원인

**문제점:**
- HoYoLAB의 동적 콘텐츠 로딩 지연으로 제목이 로드되지 않음
- 작성자 페이지에서 제목을 가져올 때 "(제목 없음)"으로 표시됨
- 로딩 대기 시간이 부족했고, 개별 포스트 페이지에서 제목을 다시 가져오는 로직의 대기 시간도 부족

**위치:** `scripts/scrape_hoyolab.py` - `fetch_posts()` 함수

## 수정 내용

### 1. 명조 특별방송 크롤링 수정 (`scripts/scrape_lounge.py`)

```python
# 이모지 제거 로직 추가
title_clean = re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', title)

# 이모지가 제거된 제목으로 키워드 매칭
is_broadcast = (
    ("프리뷰" in title_clean and "방송" in title_clean) or
    ("특별" in title_clean and "방송" in title_clean) or
    ("프리뷰" in body and "방송" in body) or
    ("특별" in body and "방송" in body)
)
```

**추가 개선사항:**
- 제목에서도 날짜를 추출하도록 fallback 로직 추가
- 더 상세한 디버깅 로그 추가

### 2. 젠존제 특별방송 크롤링 수정 (`scripts/scrape_hoyolab.py`)

**작성자 페이지 로딩 개선:**
```python
# 페이지 로딩 대기 시간 증가 (10초 → 20초)
wait = WebDriverWait(driver, 20)

# 추가 대기 시간 (동적 콘텐츠 로딩)
time.sleep(3)

# 페이지 스크롤하여 더 많은 콘텐츠 로딩
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)
driver.execute_script("window.scrollTo(0, 0);")
time.sleep(1)
```

**개별 포스트 페이지 제목 로딩 개선:**
```python
# 페이지 로딩 대기 (동적 콘텐츠)
time.sleep(3)

# h1 태그가 로드될 때까지 더 긴 시간 대기 (5초 → 10초)
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
time.sleep(2)  # 추가 대기

# 제목 업데이트
title_element = driver.find_element(By.TAG_NAME, "h1")
new_title = title_element.text.strip()
if new_title:
    post["title"] = new_title
```

**특별 방송 감지 로직 강화:**
```python
# 더 유연한 키워드 조합으로 감지
is_broadcast = (
    ("특별" in title and "방송" in title) or
    ("특별" in body and "방송" in body) or
    ("방송" in title and "예고" in title) or
    ("방송" in body and "예고" in body) or
    (ver and "방송" in title) or
    (ver and "방송" in body)
)
```

## 테스트 결과

✅ **명조 2.8 버전 프리뷰 특별 방송**
- 크롤링 성공
- URL: https://game.naver.com/lounge/WutheringWaves/board/detail/6916931
- 날짜: 2025-11-14T20:00:00+09:00
- 설명: 2.8버전 프리뷰 특별 방송

✅ **젠레스 존 제로 2.4 버전 특별 방송 예고**
- 크롤링 성공
- URL: https://www.hoyolab.com/article/42300532
- 날짜: 2025-11-14T20:30:00+09:00
- 설명: 2.4 버전 특별 방송

## 향후 특별방송 크롤링 보장

### 1. 명조 (네이버 게임 라운지)

**감지 조건:**
- 제목 또는 본문에 "프리뷰" + "방송" 키워드
- 제목 또는 본문에 "특별" + "방송" 키워드
- 이모지는 자동으로 제거되어 영향 없음

**날짜 추출:**
- 본문에서 우선 추출: `X월 X일(요일) HH:MM` 패턴
- 본문에 없으면 제목에서 추출

### 2. 젠레스 존 제로 (HoYoLAB)

**감지 조건:**
- 제목 또는 본문에 "특별" + "방송" 키워드
- 제목 또는 본문에 "방송" + "예고" 키워드
- 제목 또는 본문에 버전 정보 + "방송" 키워드

**날짜 추출:**
- 본문에서 우선 추출: `X월 X일 HH:MM(KST)` 패턴
- 본문에 없으면 제목에서 추출

**로딩 시간:**
- 작성자 페이지: 20초 대기 + 스크롤 로딩
- 개별 포스트 페이지: 10초 대기 + 3초 추가 대기

### 3. 스타레일 (HoYoLAB) - 추가 개선

동일한 HoYoLAB 플랫폼을 사용하므로, 젠존제와 동일한 로딩 시간 개선이 적용됩니다.

## GitHub Actions 적용

수정된 코드가 GitHub Actions에도 적용되었습니다:

### 수정된 파일
1. **scripts/scrape_lounge.py** - 명조 크롤링 (이모지 처리 개선)
2. **scripts/scrape_hoyolab.py** - HoYoLAB 크롤링 (로컬 테스트용)
3. **scripts/scrape_hoyolab_selenium.py** - HoYoLAB 크롤링 (GitHub Actions용, 동일한 수정 적용)

### 워크플로우
1. **scrape_lounge.yml**: 네이버 게임 라운지 (명조, 니케) - 매일 14:00 KST 실행
2. **scrape_hoyolab.yml**: HoYoLAB (젠존제, 스타레일) - 매일 13:00 KST 실행

두 워크플로우 모두 수정된 로직을 사용하여 새로운 버전의 특별방송 공지가 나올 때마다 자동으로 크롤링됩니다.

## 추가 권장사항

1. **에러 알림 설정**: GitHub Actions 실패 시 알림 설정
2. **로그 모니터링**: 정기적으로 크롤링 로그 확인
3. **새로운 패턴 추가**: 새로운 공지 형식이 나오면 즉시 패턴 추가

## 결론

두 특별방송 크롤링 실패의 주요 원인은:
1. **명조**: 이모지 처리 미비
2. **젠존제**: 동적 콘텐츠 로딩 대기 시간 부족

모두 수정되었으며, 향후 새로운 버전의 특별방송 공지가 나올 때마다 자동으로 크롤링됩니다.

