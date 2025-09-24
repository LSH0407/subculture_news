# Subculture News

서브컬처 게임들의 출시 및 업데이트 일정을 한눈에 볼 수 있는 정적 웹 애플리케이션입니다.

## 🌟 주요 기능

### 📅 달력 뷰
- **FullCalendar** 기반 월간 달력
- 게임별 업데이트/방송/신규발매 일정을 시각적으로 표시
- 하루 최대 이벤트 수 설정 가능 (5개, 10개, 15개, 20개, 제한 없음)
- 이전/다음 달 날짜도 함께 표시, 오늘 날짜 강조(틴트)
- 상단 우측 **범례**(업데이트/방송/신규발매/종료) 제공

### 🎮 게임 필터링
- **개별 게임 선택**: 니케, 명조, 원신, 붕괴: 스타레일, 젠레스 존 제로
- **Steam 게임 카테고리**: 모든 Steam 게임을 하나의 체크박스로 관리
- **닌텐도 스위치 게임 카테고리**: Switch 게임들을 별도 카테고리로 관리
- **전체 선택/해제** 기능

### 🖼️ 이벤트 표시
- **썸네일**: 기존 게임은 게임 이미지, 신작은 플랫폼 아이콘 (Steam/Switch)
- **유형별 색상**:
  - 업데이트: 파랑(#0d6efd)
  - 공식방송: 황금(#ffc107)
  - 신규발매: 초록(#198754)
  - 종료일: 빨강(#dc3545)
- **정렬**: 동일 날짜에서 Steam/Switch는 후순위(모바일/고정 게임 먼저)
- **툴팁**: 마우스 호버 시 상세 정보 표시(제목, 헤더 이미지, 태그 상위 5개, 설명). 줄바꿈 가독성 개선(pre-line)

### 🔗 상호작용
- **클릭**: Steam 게임은 Steam 스토어로, 기타 게임은 상세/공지 링크로 이동
- **달력 이미지 저장**: html2canvas로 현재 달력 뷰를 PNG로 다운로드
- **더보기(popover)**: 내부 칩도 메인과 동일한 스타일로 표시

## 🛠️ 기술 스택

### Frontend
- **HTML5**, **CSS3**(Bootstrap 5 + 커스텀), **JavaScript (ES6+)**
- **FullCalendar**, **Day.js**, **html2canvas**

### Backend & Data
- **정적 파일**: JSON 기반 데이터 저장
- **Python**: Steam 데이터 스크래핑(`scripts/scrape_comingsoon.py`)

### 외부 서비스
- **Steam API**: appdetails/스토어 태그
- **이미지 프록시**: CORS 우회 (우선 `r.jina.ai`, 폴백 `images.weserv.nl`)
- **GitHub Pages**: 정적 호스팅

## 📁 프로젝트 구조

```
subculture_news/
├── index.html              # 메인 페이지
├── detail.html             # 게임 상세 페이지 (미구현)
├── css/
│   └── style.css           # 커스텀 스타일
├── js/
│   └── main.js             # 메인 JavaScript 로직
├── data/
│   ├── games.json          # 게임 메타데이터
│   └── updates.json        # 업데이트 일정 데이터
├── assets/                 # 이미지 리소스
│   ├── nikke.png genshin.png ww.png star_rail.png zzz.png steam.png switch.png
├── scripts/
│   └── scrape_comingsoon.py # Steam 데이터 스크래핑
└── README.md               # 프로젝트 문서
```

## 🔧 데이터 구조 예시

### games.json
```json
{
  "id": "nikke",
  "name": "승리의 여신: 니케",
  "thumbnail": "assets/nikke.png"
}
```

### updates.json
```json
{
  "game_id": "nikke",
  "version": "",
  "update_date": "2025-09-24",
  "end_date": "2025-10-21",
  "description": "시작일 : 9/24\n종료일 : 10/21\n[신규] 에이다 웡",
  "url": "https://naver.me/Gq9bbVId"
}
```

### Steam 게임 데이터
```json
{
  "game_id": "steam_1234567",
  "name": "게임명",
  "update_date": "2025-10-15",
  "description": "발매예정 · 장르 · 가격",
  "platform": "steam",
  "url": "https://store.steampowered.com/app/1234567/",
  "tags": "태그1, 태그2, 태그3",
  "summary": "게임 설명",
  "header_image": "https://cdn.steamstatic.com/steam/apps/1234567/header.jpg"
}
```

## 🚀 배포

### GitHub Pages
- **URL**: https://lsh0407.github.io/subculture_news/
- **자동 배포**: main 브랜치 푸시 시 자동 업데이트
- **캐시**: 강력 캐시로 새로고침 필요할 수 있음

### 로컬 개발
```bash
# 저장소 클론
git clone https://github.com/lsh0407/subculture_news.git
cd subculture_news

# 로컬 서버 실행 (Python)
python -m http.server 8000

# 또는 Node.js
npx serve .

# 브라우저에서 접속
# http://localhost:8000
```

## 🔄 데이터 업데이트

### Steam 게임 데이터
```bash
# 수동 실행
python scripts/scrape_comingsoon.py
# 환경변수
# TARGET_MONTHS=9,10,11,12 MAX_PAGES=10 python scripts/scrape_comingsoon.py
```

### 수동 이벤트 추가
1. `data/updates.json` 편집 (시작/종료/설명/링크)
2. 커밋/푸시 → GitHub Pages 자동 반영

## 🎨 UI/UX 가이드
- **유형 색상**: 업데이트(파랑)·방송(황금)·신규발매(초록)·종료(빨강)
- **정렬 규칙**: 동일 날짜 내 Steam/Switch 후순위
- **툴팁**: 이미지 CORS 프록시 우선(`r.jina.ai`), 텍스트 줄바꿈 유지
- **가독성**: 칩 텍스트 대비 보정(text-shadow), 셀 상단 여백 보정
- **다운로드**: 설정 카드의 “달력 이미지 저장” 버튼으로 PNG 저장
- **범례**: 제목 바 우측 색 점으로 의미 안내

## 📞 문의 및 지원
- **Discord**: [문의하기](https://discord.com/channels/1402629632142086235/1420232300070965370)
- **GitHub**: [이슈 리포트](https://github.com/lsh0407/subculture_news/issues)
- **라이선스**: MIT

---

**Subculture News** - 서브컬처 게임 커뮤니티를 위한 일정 관리 도구