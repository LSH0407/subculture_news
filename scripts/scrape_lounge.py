import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


KST_OFFSET = "+09:00"


def get_selenium_driver():
    """Selenium WebDriver 설정 (webdriver-manager 사용)"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (compatible; subculture-news/1.0)")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # 환경에 따른 추가 옵션 (GitHub Actions에서만 적용)
    import os
    if os.getenv('GITHUB_ACTIONS'):
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--remote-debugging-port=9223")  # 다른 포트 사용
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    
    try:
        # webdriver-manager를 사용하여 ChromeDriver 자동 관리
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"WebDriver Manager failed, trying default: {e}")
        driver = webdriver.Chrome(options=chrome_options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def get(url: str) -> BeautifulSoup:
    """기존 requests 방식 (fallback)"""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def get_with_selenium(url: str, wait_time: int = 10, driver=None) -> BeautifulSoup:
    """Selenium을 사용한 JavaScript 렌더링"""
    should_quit = False
    if driver is None:
        driver = get_selenium_driver()
        should_quit = True
    
    try:
        driver.get(url)
        # 페이지 로딩 대기
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # 추가 대기 (동적 콘텐츠 로딩)
        time.sleep(2)  # 3초에서 2초로 단축
        html = driver.page_source
        return BeautifulSoup(html, "html.parser")
    finally:
        if should_quit:
            driver.quit()


def kor_dt(text: str) -> Tuple[str, str]:
    # 패턴 1: X월 X일(요일) HH:MM (가장 일반적)
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*\([^)]+\)\s*(\d{1,2}):(\d{2})", text)
    if m:
        mm, dd, hh, mi = m.group(1), m.group(2), m.group(3), m.group(4)
        year = datetime.now().year
        return f"{year}-{int(mm):02d}-{int(dd):02d}T{int(hh):02d}:{int(mi):02d}:00{KST_OFFSET}", f"{int(mm)}/{int(dd)} {int(hh):02d}:{int(mi):02d}"
    
    # 패턴 2: X/X(요일) HH:MM
    m = re.search(r"(\d{1,2})/(\d{1,2})\s*\([^)]+\)\s*(\d{1,2}):(\d{2})", text)
    if m:
        mm, dd, hh, mi = m.group(1), m.group(2), m.group(3), m.group(4)
        year = datetime.now().year
        return f"{year}-{int(mm):02d}-{int(dd):02d}T{int(hh):02d}:{int(mi):02d}:00{KST_OFFSET}", f"{int(mm)}/{int(dd)} {int(hh):02d}:{int(mi):02d}"
    
    # 패턴 3: X월 X일 HH:MM (KST) - 기존 패턴
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*(\d{1,2})(?::(\d{2}))?\s*\(K?ST\)?", text)
    if m:
        mm, dd, hh, mi = m.group(1), m.group(2), m.group(3), m.group(4) or "00"
        year = datetime.now().year
        return f"{year}-{int(mm):02d}-{int(dd):02d}T{int(hh):02d}:{int(mi):02d}:00{KST_OFFSET}", f"{int(mm)}/{int(dd)} {int(hh):02d}:{int(mi):02d}"
    
    # 패턴 4: X월 X일만 (시간 없음)
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if m:
        mm, dd = m.group(1), m.group(2)
        year = datetime.now().year
        return f"{year}-{int(mm):02d}-{int(dd):02d}", f"{int(mm)}/{int(dd)}"
    
    return "", ""


def kor_range(text: str) -> Tuple[str, str]:
    # 패턴 1: YYYY년 X월 X일 HH:MM ~ YYYY년 X월 X일 HH:MM (시간 포함)
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*\d{1,2}:\d{2}\s*[~\-–—]\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*\d{1,2}:\d{2}", text)
    if m:
        s = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        e = f"{m.group(4)}-{int(m.group(5)):02d}-{int(m.group(6)):02d}"
        return s, e
    
    # 패턴 2: YYYY년 X월 X일 ~ YYYY년 X월 X일 (시간 없음)
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*[~\-–—]\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", text)
    if m:
        s = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        e = f"{m.group(4)}-{int(m.group(5)):02d}-{int(m.group(6)):02d}"
        return s, e
    
    # 패턴 3: X월 X일 ~ X월 X일
    m = re.search(r"(\d{1,2})월\s*(\d{1,2})일\s*[~\-–—]\s*(\d{1,2})월\s*(\d{1,2})일", text)
    if m:
        y = datetime.now().year
        s = f"{y}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        e = f"{y}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
        return s, e
    
    # 패턴 4: 업데이트 이후 ~ YYYY년 X월 X일 (명조 특화)
    m = re.search(r"업데이트\s*이후.*?(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", text)
    if m:
        # 종료일은 추출 가능
        e = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        # 시작일은 버전 업데이트 공지에서 찾아야 함 (parse_ww에서 처리)
        return "", e
    
    return "", ""


def fetch_board_posts(board_url: str, max_items: int = 20) -> List[Dict]:
    """게시판 게시글 수집 (Selenium 사용, 최적화된 버전)"""
    driver = None
    try:
        # 하나의 드라이버 인스턴스로 모든 작업 수행
        driver = get_selenium_driver()
        
        # Selenium으로 JavaScript 렌더링된 페이지 가져오기 (SPA 대응)
        print(f"Loading SPA page with Selenium: {board_url}")
        driver.get(board_url)
        
        # SPA 로딩 대기 (더 긴 시간)
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        try:
            wait = WebDriverWait(driver, 20)
            # 게시글 제목이 로드될 때까지 대기
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class*='title']")))
            print("SPA content loaded successfully")
        except Exception as e:
            print(f"SPA loading timeout, proceeding anyway: {e}")
        
        # 추가 안전 대기
        time.sleep(5)
        
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(f"Selenium failed for {board_url}, falling back to requests: {e}")
        # Fallback to requests
        soup = get(board_url)
    
    posts: List[Dict] = []
    
    # 네이버 게임 라운지 게시글 제목 선택자 사용 (SPA 대응)
    # 다양한 선택자로 게시글 제목 링크 찾기
    title_links = soup.select("a[class*='title']")
    if not title_links:
        # fallback 선택자들
        title_links = soup.find_all("a", class_=lambda x: x and "post_board_title" in x)
    if not title_links:
        title_links = soup.select("a[href*='detail']")
    
    print(f"Found {len(title_links)} title links from {board_url}")
    
    for a in title_links:
        title = a.get_text(strip=True)
        href = a.get("href")
        
        if not title or not href:
            continue
            
        # 상대 경로를 절대 경로로 변환
        if href.startswith("/"):
            href = f"https://game.naver.com{href}"
        
        # detail 링크만 수집 (실제 게시글)
        if "detail" not in href:
            continue
        
        # 중복 제거
        if not any(p["url"] == href for p in posts):
            posts.append({"title": title, "url": href})
            
        if len(posts) >= max_items:
            break
    
    print(f"Collected {len(posts)} posts")
    
    # 본문 수집 (같은 드라이버 인스턴스 재사용)
    if driver:
        for i, p in enumerate(posts):
            try:
                print(f"  -> Getting body for post {i+1}/{len(posts)}: {p['url']}")
                ps = get_with_selenium(p["url"], wait_time=8, driver=driver)  # 대기 시간 단축
                body_text = ps.get_text("\n", strip=True)
                p["body"] = body_text
                
                # 특수모집 관련 키워드가 있는지 확인
                if any(keyword in body_text for keyword in ['특수모집', '합류', '모집에 합류']):
                    print(f"    *** Found recruit keywords in body! ***")
                    
            except Exception as e:
                print(f"Failed to get body for {p['url']}: {e}")
                p["body"] = ""
    else:
        # Selenium이 실패한 경우 requests로 본문 수집 시도
        for i, p in enumerate(posts):
            try:
                print(f"  -> Getting body for post {i+1}/{len(posts)} (requests): {p['url']}")
                ps = get(p["url"])
                body_text = ps.get_text("\n", strip=True)
                p["body"] = body_text
            except Exception as e:
                print(f"Failed to get body for {p['url']}: {e}")
                p["body"] = ""
    
    # 드라이버 정리
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    return posts


def parse_nikke(board_update_url: str, board_broadcast_url: str, limit: int = 20) -> List[Dict]:
    out: List[Dict] = []
    # 업데이트 소식 사전 안내 - 모집
    update_posts = fetch_board_posts(board_update_url, limit)
    try:
        print(f"Nikke update board posts: {len(update_posts)}")
        for i, p in enumerate(update_posts[:3]):
            print(f"  {i+1}. {p['title'][:60]}")
    except Exception:
        pass  # 인코딩 오류 무시
    
    for i, p in enumerate(update_posts):
        try:
            print(f"Parsing post {i+1}/{len(update_posts)}: {p['title'][:50]}...")
        except:
            print(f"Parsing post {i+1}/{len(update_posts)}: [encoding error in title]")
            
        # 특수모집 합류 감지 로직 개선
        title_lower = p["title"].lower()
        body_lower = p.get("body", "").lower()
        
        # 다양한 패턴으로 특수모집 합류 감지 (더 유연한 조건)
        body = p.get("body", "")
        title = p["title"]
        
        is_recruit_post = (
            # 조건 1: 업데이트 소식 사전 안내 + 모집 관련 키워드
            ("업데이트 소식 사전 안내" in title and ("모집에 합류" in body or "특수 모집" in body or ("모집" in body and "합류" in body))) or
            # 조건 2: 제목에 특수모집 + 합류
            ("특수모집" in title and "합류" in title) or
            # 조건 3: 본문에 특수모집 + 합류 (띄어쓰기 고려)
            (("특수모집" in body or "특수 모집" in body) and "합류" in body) or
            # 조건 4: 캐릭터 특수모집
            ("캐릭터 특수모집" in title) or
            ("캐릭터 특수모집" in body) or
            # 조건 5: SSR + 합류 (니케 특화)
            ("SSR" in body and "합류" in body and "업데이트 소식 사전 안내" in title)
        )
        
        # 각 조건 확인
        cond1 = "업데이트 소식 사전 안내" in title and ("모집에 합류" in body or "특수 모집" in body or ("모집" in body and "합류" in body))
        cond2 = "특수모집" in title and "합류" in title
        cond3 = ("특수모집" in body or "특수 모집" in body) and "합류" in body
        cond4 = "캐릭터 특수모집" in title
        cond5 = "캐릭터 특수모집" in body
        cond6 = "SSR" in body and "합류" in body and "업데이트 소식 사전 안내" in title
        
        if any([cond1, cond2, cond3, cond4, cond5, cond6]):
            print(f"  Recruit conditions: cond1={cond1}, cond2={cond2}, cond3={cond3}, cond4={cond4}, cond5={cond5}, cond6={cond6}")
            print(f"  URL: {p['url']}")
            print(f"  Body length: {len(p.get('body', ''))}")
            if "특수모집" in p.get("body", ""):
                print(f"  Body contains '특수모집'")
            if "특수 모집" in p.get("body", ""):
                print(f"  Body contains '특수 모집'")
            if "합류" in p.get("body", ""):
                print(f"  Body contains '합류'")
            if "SSR" in p.get("body", ""):
                print(f"  Body contains 'SSR'")
        
        if is_recruit_post:
            try:
                print(f"Found recruit post: {p['title']}")
            except:
                print("Found recruit post: [encoding error in title]")
                
            body = p["body"]
            print(f"  Body length: {len(body)}")
            
            # 여러 특수모집을 찾기 위해 본문을 분할
            # "기간 한정 모집" 또는 "특수 모집"으로 구분된 섹션들을 처리
            try:
                # 모든 SSR 니케 캐릭터 찾기
                ssr_characters = re.findall(r"SSR\s*니케\s*\[([^\]]+)\]", body)
                print(f"  Found {len(ssr_characters)} SSR NIKKE characters: {ssr_characters}")
                
                if not ssr_characters:
                    # fallback: SSR [...] 패턴
                    ssr_characters = re.findall(r"SSR[^[]*\[([^\]]+)\]", body)
                    print(f"  Fallback pattern found {len(ssr_characters)} characters: {ssr_characters}")
                
                # 각 캐릭터에 대해 개별적으로 날짜 정보 찾기
                for char_name in ssr_characters:
                    print(f"\n  Processing character: {char_name}")
                    
                    # 해당 캐릭터 섹션 추출
                    # 캐릭터명이 나온 이후 ~ 다음 SSR 니케가 나오기 전까지
                    char_pattern = rf"\[{re.escape(char_name)}\]"
                    char_idx = body.find(f"[{char_name}]")
                    
                    if char_idx == -1:
                        print(f"    Character name not found in body, skipping")
                        continue
                    
                    # 다음 SSR 니케가 나올 때까지의 섹션 (없으면 끝까지)
                    next_ssr_idx = body.find("SSR 니케", char_idx + len(char_name) + 50)
                    if next_ssr_idx == -1:
                        char_section = body[char_idx:]
                    else:
                        char_section = body[char_idx:next_ssr_idx]
                    
                    print(f"    Character section length: {len(char_section)}")
                    
                    # 모집 기간 찾기: YYYY년 MM월 DD일 ... ~ YYYY년 MM월 DD일
                    date_range_pattern = r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일[^~]*?~[^~]*?(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일"
                    date_match = re.search(date_range_pattern, char_section)
                    
                    if date_match:
                        y1, m1, d1, y2, m2, d2 = date_match.groups()
                        start_date = f"{y1}-{int(m1):02d}-{int(d1):02d}"
                        end_date = f"{y2}-{int(m2):02d}-{int(d2):02d}"
                        print(f"    Found date range: {start_date} ~ {end_date}")
                        
                        # 한글 날짜 표시
                        start_month = int(m1)
                        start_day = int(d1)
                        end_month = int(m2)
                        end_day = int(d2)
                        
                        description = f"시작일 : {start_month}월 {start_day}일\n종료일 : {end_month}월 {end_day}일\n[신규] {char_name} 특수모집"
                        
                        result = {
                            "game_id": "nikke",
                            "version": "",
                            "update_date": start_date,
                            "end_date": end_date,
                            "description": description,
                            "url": p["url"],
                        }
                        out.append(result)
                        try:
                            print(f"    *** Added recruit update for {char_name}")
                        except:
                            print(f"    *** Added recruit update: [encoding error]")
                    else:
                        print(f"    No date range found for {char_name}")
                        
            except Exception as e:
                print(f"  Multiple recruit parsing failed: {e}")
                import traceback
                traceback.print_exc()
    
    # 특별 방송 안내 (패턴 완화)
    broadcast_posts = fetch_board_posts(board_broadcast_url, limit)
    try:
        print(f"Nikke broadcast board posts: {len(broadcast_posts)}")
        for i, p in enumerate(broadcast_posts[:3]):
            print(f"  {i+1}. {p['title'][:60]}")
    except Exception:
        pass  # 인코딩 오류 무시
    
    for p in broadcast_posts:
        # "방송" + "사전" + "안내" 키워드로 탐지
        if ("방송" in p["title"] and "사전" in p["title"] and "안내" in p["title"]) or \
           ("방송" in p["title"] and "안내" in p["title"]):
            try:
                print(f"Found broadcast post: {p['title']}")
            except Exception:
                pass
            body = p.get("body", "")
            dt_iso, _ = kor_dt(body)
            if dt_iso:
                out.append({
                    "game_id": "nikke",
                    "version": "",
                    "update_date": dt_iso,
                    "description": "특별 방송",
                    "url": p["url"],
                })
            else:
                try:
                    print(f"  No date found in body (length: {len(body)})")
                except Exception:
                    pass
    return out


def parse_ww(board_tuning_url: str, board_broadcast_url: str, limit: int = 20) -> List[Dict]:
    out: List[Dict] = []
    posts_tuning = fetch_board_posts(board_tuning_url, limit)
    try:
        print(f"WW tuning board posts: {len(posts_tuning)}")
        for i, p in enumerate(posts_tuning[:3]):
            print(f"  {i+1}. {p['title'][:60]}")
    except Exception:
        pass  # 인코딩 오류 무시
    
    posts_notice = {p["title"]: p for p in posts_tuning}
    for p in posts_tuning:
        # "캐릭터 이벤트 튜닝"만 필터링 (무기 이벤트 튜닝 제외)
        if "캐릭터" in p["title"] and "이벤트" in p["title"] and "튜닝" in p["title"]:
            # 제목에 "무기" 키워드가 있으면 제외 (본문의 "무기"는 무시)
            if "무기" in p["title"] and "캐릭터" not in p["title"]:
                continue
            try:
                print(f"Found tuning post: {p['title']}")
            except Exception:
                pass
            body = p.get("body", "")
            start, end = kor_range(body)
            
            # 버전 파싱: "X.X 버전 업데이트 이후" 패턴을 우선 검색
            ver = ""
            if "업데이트 이후" in body:
                update_after_match = re.search(r"(\d+\.\d+)\s*버전\s*업데이트\s*이후", body)
                if update_after_match:
                    ver = update_after_match.group(1)
            
            # 버전을 못 찾았으면 일반 패턴으로 검색
            if not ver:
                ver_match = re.search(r"(\d+(?:\.\d+)?)\s*버전", p["title"] + " " + body)
                ver = ver_match.group(1) if ver_match else ""
            
            # 시작일이 없고 "X.X 버전 업데이트 이후"가 있는 경우
            if not start and end and "업데이트 이후" in body and ver:
                # "X.X 버전 업데이트 점검 사전 공지" 게시글에서 점검 종료 시간 찾기
                for t, post in posts_notice.items():
                    if "업데이트 점검 사전 공지" in t and ver in t:
                        notice_body = post.get("body", "")
                        # 점검 시간 패턴: YYYY년 X월 X일 HH:MM ~ YYYY년 X월 X일 HH:MM
                        time_pattern = re.search(
                            r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*\d{1,2}:\d{2}\s*[~\-–—]\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*\d{1,2}:\d{2}",
                            notice_body
                        )
                        if time_pattern:
                            # 종료 시간의 날짜 사용 (연도, 월, 일)
                            end_year = time_pattern.group(4)
                            end_month = int(time_pattern.group(5))
                            end_day = int(time_pattern.group(6))
                            start = f"{end_year}-{end_month:02d}-{end_day:02d}"
                            try:
                                print(f"  Found version {ver} update date from notice: {start}")
                            except Exception:
                                pass
                        break
                    
            if start and end:
                # 한글 날짜 표시
                start_month = int(start[5:7])
                start_day = int(start[8:10])
                end_month = int(end[5:7])
                end_day = int(end[8:10])
                
                # 캐릭터 이름 추출 (「캐릭터명」 패턴)
                char_match = re.search(r"「(.+?)」", p["title"])
                char_name = char_match.group(1) if char_match else ""
                
                # 설명 구성
                desc_parts = [
                    f"시작일 : {start_month}월 {start_day}일",
                    f"종료일 : {end_month}월 {end_day}일",
                ]
                if char_name:
                    desc_parts.append(f"[5성] {char_name}")
                else:
                    desc_parts.append("[이벤트] 캐릭터 이벤트 튜닝")
                
                out.append({
                    "game_id": "ww",
                    "version": ver,
                    "update_date": start,
                    "end_date": end,
                    "description": "\n".join(desc_parts),
                    "url": p["url"],
                })
            else:
                try:
                    print(f"  No date range found (start={start}, end={end})")
                except Exception:
                    pass

    # 프리뷰 특별 방송 (패턴 완화)
    broadcast_posts = fetch_board_posts(board_broadcast_url, limit)
    try:
        print(f"WW broadcast board posts: {len(broadcast_posts)}")
        for i, p in enumerate(broadcast_posts[:3]):
            print(f"  {i+1}. {p['title'][:60]}")
    except Exception:
        pass  # 인코딩 오류 무시
    
    for p in broadcast_posts:
        # 제목과 본문 모두에서 키워드 검색 (패턴 완화)
        title = p["title"]
        body = p.get("body", "")
        
        # 이모지 제거 (유니코드 이모지 범위)
        title_clean = re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', title)
        
        # "프리뷰" + "방송" 또는 "특별" + "방송" 키워드로 완화
        # 제목 또는 본문에 키워드가 있으면 감지
        is_broadcast = (
            ("프리뷰" in title_clean and "방송" in title_clean) or
            ("특별" in title_clean and "방송" in title_clean) or
            ("프리뷰" in body and "방송" in body) or
            ("특별" in body and "방송" in body)
        )
        
        if is_broadcast:
            # "시작됩니다"가 포함된 제목은 과거 공지이므로 스킵
            if "시작됩니다" in title_clean:
                continue
            try:
                print(f"Found broadcast post: {title}")
            except Exception:
                pass
            
            # 본문에서 날짜 추출 (제목에서도 시도)
            dt_iso, _ = kor_dt(body)
            if not dt_iso:
                dt_iso, _ = kor_dt(title_clean)
            
            if dt_iso:
                # 버전 추출 시도 (제목과 본문 모두에서)
                ver_match = re.search(r"(\d+\.\d+)\s*버전", title_clean + " " + body)
                ver = ver_match.group(1) if ver_match else ""
                
                desc = f"{ver}버전 프리뷰 특별 방송" if ver else "프리뷰 특별 방송"
                
                out.append({
                    "game_id": "ww",
                    "version": ver,
                    "update_date": dt_iso,
                    "description": desc,
                    "url": p["url"],
                })
                try:
                    print(f"  *** Added broadcast: {desc} on {dt_iso}")
                except Exception:
                    pass
            else:
                try:
                    print(f"  No date found in title or body (body length: {len(body)})")
                except Exception:
                    pass
    return out


def merge(updates: List[Dict]) -> None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "updates.json"))
    try:
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []
    def key(u: Dict) -> str:
        return f"{u.get('game_id')}|{u.get('version','')}|{u.get('update_date')}|{u.get('description','')[:40]}"
    seen = {key(u) for u in existing}
    merged = existing[:]
    add = 0
    for u in updates:
        if key(u) in seen:
            continue
        merged.append(u)
        add += 1
    if add:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Lounge merged: +{add}")


def main():
    # Naver Game Lounge boards
    nikke_update = os.getenv("NIKKE_UPDATE_BOARD", "https://game.naver.com/lounge/nikke/board/48")
    nikke_broadcast = os.getenv("NIKKE_BROADCAST_BOARD", "https://game.naver.com/lounge/nikke/board/11")
    ww_tuning = os.getenv("WW_TUNING_BOARD", "https://game.naver.com/lounge/WutheringWaves/board/28")
    ww_broadcast = os.getenv("WW_BROADCAST_BOARD", "https://game.naver.com/lounge/WutheringWaves/board/1")
    limit = int(os.getenv("LOUNGE_LIMIT", "20"))

    updates: List[Dict] = []
    try:
        updates += parse_nikke(nikke_update, nikke_broadcast, limit)
    except Exception as e:
        print("Nikke parse failed:", e)
    try:
        updates += parse_ww(ww_tuning, ww_broadcast, limit)
    except Exception as e:
        print("WW parse failed:", e)

    merge(updates)


if __name__ == "__main__":
    main()


