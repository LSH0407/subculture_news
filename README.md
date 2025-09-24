# Subculture News

서브컬처 게임들의 출시 및 업데이트 일정을 한눈에 볼 수 있는 정적 웹 애플리케이션입니다.

## 🌟 주요 기능

### 📅 달력 뷰
- **FullCalendar** 기반 월간 달력
- 게임별 업데이트 일정을 시각적으로 표시
- 하루 최대 이벤트 수 설정 가능 (5개, 10개, 15개, 20개, 제한 없음)
- 이전/다음 달 날짜도 함께 표시

### 🎮 게임 필터링
- **개별 게임 선택**: 니케, 림버스, 명조, 원신, 스타레일, 젠레스존제로
- **Steam 게임 카테고리**: 모든 Steam 게임을 하나의 체크박스로 관리
- **닌텐도 스위치 게임 카테고리**: Switch 게임들을 별도 카테고리로 관리
- **전체 선택/해제** 기능

### 🖼️ 이벤트 표시
- **썸네일**: 기존 게임은 게임 이미지, 신작은 플랫폼 아이콘 (Steam/Switch)
- **게임명**: 텍스트 오버플로우 처리로 깔끔한 표시
- **툴팁**: 마우스 호버 시 상세 정보 표시
  - 게임 제목 (전체)
  - 헤더 이미지 (Steam/Switch 게임)
  - 인기 태그 (상위 5개)
  - 게임 설명

### 🔗 상호작용
- **클릭**: Steam 게임은 Steam 스토어로, 기타 게임은 상세 페이지로 이동
- **반응형 디자인**: 모바일/데스크톱 최적화

## 🛠️ 기술 스택

### Frontend
- **HTML5**: 시맨틱 마크업
- **CSS3**: Bootstrap 5 + 커스텀 스타일
- **JavaScript (ES6+)**: 바닐라 JS (모듈 없음)
- **FullCalendar**: 달력 라이브러리
- **Day.js**: 날짜/시간 처리

### Backend & Data
- **정적 파일**: JSON 기반 데이터 저장
- **Python**: Steam 데이터 스크래핑
- **GitHub Actions**: 자동화된 데이터 업데이트

### 외부 서비스
- **Steam API**: 게임 정보 및 헤더 이미지
- **이미지 프록시**: CORS 우회 (r.jina.ai, images.weserv.nl)
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
│   ├── nikke.png
│   ├── genshin.png
│   ├── ww.png
│   ├── star_rail.png
│   ├── zzz.png
│   ├── limbus.png
│   ├── steam.png
│   └── switch.png
├── scripts/
│   └── scrape_comingsoon.py # Steam 데이터 스크래핑
└── README.md               # 프로젝트 문서
```

## 🎯 지원 게임

### 모바일 게임
- **승리의 여신: 니케** - 바이오하자드 콜라보 이벤트
- **붕괴: 스타레일** - 버전 업데이트 및 픽업
- **젠레스 존 제로** - 신규 캐릭터 픽업
- **원신** - 버전 업데이트
- **명조 (Wuthering Waves)** - 업데이트
- **림버스 컴퍼니** - 업데이트

### PC 게임 (Steam)
- **인기 찜 목록** 기준 발매예정 게임들
- 9-10월 발매예정 게임 중심
- 한국어 지역화 정보 포함

### 콘솔 게임 (Nintendo Switch)
- **포켓몬 LEGENDS Z-A** - 2025년 10월 16일 발매예정

## 🔧 데이터 구조

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
  "update_date": "2025-09-24T00:00:00+09:00",
  "end_date": "2025-09-24T07:00:00+09:00",
  "description": "바이오하자드 콜라보 업데이트 · SSR 에이다 웡 픽업 시작"
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
- **캐시**: 브라우저 새로고침 필요할 수 있음

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

# GitHub Actions (자동)
# 매일 실행되어 최신 Steam 게임 정보 수집
```

### 수동 이벤트 추가
1. `data/updates.json` 파일 편집
2. Git 커밋 및 푸시
3. GitHub Pages 자동 배포

## 🎨 UI/UX 특징

### 달력 디자인
- **Bootstrap 5** 기반 모던한 디자인
- **반응형 그리드** 레이아웃
- **커스텀 이벤트 칩** 스타일링
- **툴팁** 상호작용

### 색상 테마
- **Primary**: Bootstrap Blue (#0d6efd)
- **일관된 색상**: 모든 이벤트에 동일한 테마 적용
- **접근성**: 충분한 대비와 가독성

### 반응형 디자인
- **모바일**: 터치 친화적 인터페이스
- **태블릿**: 중간 크기 최적화
- **데스크톱**: 전체 기능 활용

## 🔍 주요 기능 상세

### 필터링 시스템
- **다중 선택**: 여러 게임 동시 선택 가능
- **카테고리 그룹핑**: Steam/Switch 게임을 카테고리로 관리
- **실시간 업데이트**: 필터 변경 시 즉시 달력 반영

### 이미지 처리
- **Steam 게임**: 프록시 서버를 통한 CORS 우회
- **Switch 게임**: 직접 이미지 로드
- **폴백 시스템**: 이미지 로딩 실패 시 대체 이미지

### 성능 최적화
- **지연 로딩**: 이미지 lazy loading
- **캐싱**: 브라우저 캐시 활용
- **압축**: 정적 파일 최적화

## 📞 문의 및 지원

- **Discord**: [문의하기](https://discord.com/channels/1402629632142086235/1420232300070965370)
- **GitHub**: [이슈 리포트](https://github.com/lsh0407/subculture_news/issues)
- **라이선스**: MIT

## 🔮 향후 계획

- [ ] 게임 상세 페이지 구현
- [ ] 알림 기능 추가
- [ ] 더 많은 플랫폼 지원 (PlayStation, Xbox)
- [ ] 사용자 맞춤 설정 저장
- [ ] 다국어 지원
- [ ] PWA (Progressive Web App) 변환

---

**Subculture News** - 서브컬처 게임 커뮤니티를 위한 일정 관리 도구