# 네이버 게임 라운지 스크래퍼 문제 해결 가이드

## 문제 상황
네이버 게임 라운지 동기화 액션이 실행되지만 새로운 게시글이 감지되지 않음 (`changes: 0+0-`)

## 원인 분석
네이버 게임 라운지가 **SPA(Single Page Application)**로 변경되어 JavaScript 동적 로딩이 필요합니다:
- 모든 URL이 동일한 HTML 반환 (4958자)
- 실제 콘텐츠는 `<div id="root"></div>`에 JavaScript로 동적 삽입
- React 기반 웹앱으로 변경됨

## 해결 방안
Selenium WebDriver를 사용한 JavaScript 렌더링 지원으로 수정 완료:
- ✅ Selenium + Chrome 환경 구축
- ✅ webdriver-manager로 ChromeDriver 자동 관리
- ✅ 봇 탐지 방지 옵션 추가
- ✅ requests fallback 유지

## 테스트 방법

### 1. 깃허브 액션 수동 실행
1. 깃허브 저장소 페이지 이동: https://github.com/LSH0407/subculture_news
2. **Actions** 탭 클릭
3. **Scrape Naver Game Lounge** 워크플로우 선택
4. **Run workflow** 버튼 클릭
5. **Run workflow** 확인

### 2. 로그 확인
워크플로우 실행 후 다음 항목들을 확인:
- Install Chrome 단계 성공 여부
- Run Lounge scraper 단계 출력
  - `Found X posts from ...` 메시지 확인
  - 파싱 결과 메시지 확인
- Commit changes 단계에서 변경사항 유무

### 3. 로컬 테스트 (Windows)
**주의**: Windows 환경에서는 Selenium 포트 바인딩 오류가 발생할 수 있습니다.

```bash
# Selenium 설치 (이미 설치되어 있음)
pip install selenium webdriver-manager

# Chrome 브라우저 설치 확인 필요
# 스크립트 실행 (매우 느릴 수 있음)
python scripts/scrape_lounge.py
```

## 예상되는 결과

### 성공 시
```bash
Found 10 posts from https://game.naver.com/lounge/nikke/board/48
Found 10 posts from https://game.naver.com/lounge/nikke/board/11
Found 10 posts from https://game.naver.com/lounge/WutheringWaves/board/28
Found 10 posts from https://game.naver.com/lounge/WutheringWaves/board/1
Lounge merged: +2
```

### 실패 시
- ChromeDriver 설치 오류
- Selenium WebDriver 초기화 실패
- 타임아웃 오류
- 네트워크 오류

## 목표 게시글 확인
다음 게시글들이 정상적으로 크롤링되어야 합니다:

### 명조 (WutheringWaves)
- **게시판**: 업데이트 소식 (board/28)
- **목표 게시글**: https://game.naver.com/lounge/WutheringWaves/board/detail/6767962
- **예상 내용**: 캐릭터 이벤트 튜닝 관련

### 니케 (NIKKE)
- **게시판**: 방송/영상 (board/11)
- **목표 게시글**: https://game.naver.com/lounge/nikke/board/detail/6767886
- **예상 내용**: 특별 방송 안내

## 트러블슈팅

### ChromeDriver 버전 불일치
```bash
# webdriver-manager가 자동으로 관리하므로 수동 개입 불필요
```

### Selenium 타임아웃
스크립트에서 대기 시간 증가:
```python
# scripts/scrape_lounge.py
soup = get_with_selenium(url, wait_time=15)  # 기본 10초 -> 15초
```

### 메모리 부족
깃허브 액션 환경에서는 충분한 메모리가 있지만, 로컬 테스트 시:
- Chrome을 헤드리스 모드로 실행 (이미 설정됨)
- 동시 실행 제한

## 주요 변경 사항

### .github/workflows/scrape_lounge.yml
- Selenium 의존성 추가
- Chrome 브라우저 자동 설치
- webdriver-manager 추가

### scripts/scrape_lounge.py
- `get_selenium_driver()`: Selenium WebDriver 설정
- `get_with_selenium()`: JavaScript 렌더링 지원
- `fetch_board_posts()`: 다양한 CSS 선택자로 게시글 검색

## 문의
문제가 지속되면 깃허브 액션 로그를 확인하거나 이슈를 생성해주세요.

---
**마지막 업데이트**: 2025-10-08
**수정 버전**: Selenium + webdriver-manager
