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
    
    # webdriver-manager를 사용하여 ChromeDriver 자동 관리
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def get(url: str) -> BeautifulSoup:
    """기존 requests 방식 (fallback)"""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def get_with_selenium(url: str, wait_time: int = 10) -> BeautifulSoup:
    """Selenium을 사용한 JavaScript 렌더링"""
    driver = get_selenium_driver()
    try:
        driver.get(url)
        # 페이지 로딩 대기
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # 추가 대기 (동적 콘텐츠 로딩)
        time.sleep(3)
        html = driver.page_source
        return BeautifulSoup(html, "html.parser")
    finally:
        driver.quit()


def kor_dt(text: str) -> Tuple[str, str]:
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*(\d{1,2})(?::(\d{2}))?\s*\(K?ST\)?", text)
    if m:
        mm, dd, hh, mi = m.group(1), m.group(2), m.group(3), m.group(4) or "00"
        year = datetime.now().year
        return f"{year}-{int(mm):02d}-{int(dd):02d}T{int(hh):02d}:{int(mi):02d}:00{KST_OFFSET}", f"{int(mm)}/{int(dd)} {int(hh):02d}:{int(mi):02d}"
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if m:
        mm, dd = m.group(1), m.group(2)
        year = datetime.now().year
        return f"{year}-{int(mm):02d}-{int(dd):02d}", f"{int(mm)}/{int(dd)}"
    return "", ""


def kor_range(text: str) -> Tuple[str, str]:
    m = re.search(r"(\d{1,2})월\s*(\d{1,2})일\s*[~\-]\s*(\d{1,2})월\s*(\d{1,2})일", text)
    if not m:
        return "", ""
    y = datetime.now().year
    s = f"{y}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    e = f"{y}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
    return s, e


def fetch_board_posts(board_url: str, max_items: int = 20) -> List[Dict]:
    """게시판 게시글 수집 (Selenium 사용)"""
    try:
        # Selenium으로 JavaScript 렌더링된 페이지 가져오기
        soup = get_with_selenium(board_url)
    except Exception as e:
        print(f"Selenium failed for {board_url}, falling back to requests: {e}")
        # Fallback to requests
        soup = get(board_url)
    
    posts: List[Dict] = []
    
    # 다양한 선택자로 게시글 링크 찾기
    selectors = [
        "a[href*='board']",
        "a[href*='article']", 
        ".board-list a",
        ".post-list a",
        ".article-list a",
        "a"
    ]
    
    for selector in selectors:
        links = soup.select(selector)
        for a in links:
            title = a.get_text(strip=True)
            href = a.get("href")
            if not title or not href or len(title) < 5:
                continue
            if href.startswith("/"):
                href = f"https://game.naver.com{href}"
            if "board" not in href and "article" not in href:
                continue
            # 중복 제거
            if not any(p["url"] == href for p in posts):
                posts.append({"title": title, "url": href})
            if len(posts) >= max_items:
                break
        if len(posts) >= max_items:
            break
    
    print(f"Found {len(posts)} posts from {board_url}")
    
    # 본문 수집 (Selenium 사용)
    for p in posts:
        try:
            ps = get_with_selenium(p["url"], wait_time=5)
            p["body"] = ps.get_text("\n", strip=True)
        except Exception as e:
            print(f"Failed to get body for {p['url']}: {e}")
            p["body"] = ""
    
    return posts


def parse_nikke(board_update_url: str, board_broadcast_url: str, limit: int = 20) -> List[Dict]:
    out: List[Dict] = []
    # 업데이트 소식 사전 안내 - 모집
    update_posts = fetch_board_posts(board_update_url, limit)
    print(f"Nikke update board posts: {len(update_posts)}")
    for i, p in enumerate(update_posts[:3]):
        print(f"  {i+1}. {p['title'][:60]}")
    
    for p in update_posts:
        if "업데이트 소식 사전 안내" in p["title"] and "모집에 합류" in p.get("body", ""):
            body = p["body"]
            # SSR ... ] 패턴
            m = re.search(r"(SSR[^\]]+\])", body)
            recruit = m.group(1) if m else "모집"
            # 모집기간 라인에서 날짜 범위 추출
            s, e = kor_range(body)
            if not (s and e):
                # 단일 날짜들만 있는 경우 첫/둘째 날짜 시도
                dates = re.findall(r"(\d{1,2})월\s*(\d{1,2})일", body)
                if len(dates) >= 2:
                    y = datetime.now().year
                    s = f"{y}-{int(dates[0][0]):02d}-{int(dates[0][1]):02d}"
                    e = f"{y}-{int(dates[1][0]):02d}-{int(dates[1][1]):02d}"
            if s and e:
                out.append({
                    "game_id": "nikke",
                    "version": "",
                    "update_date": s,
                    "end_date": e,
                    "description": f"시작일 : {int(s[5:7])}/{int(s[8:10])}\n종료일 : {int(e[5:7])}/{int(e[8:10])}\n[신규] {recruit}",
                    "url": p["url"],
                })
    
    # 특별 방송 안내 (패턴 완화)
    broadcast_posts = fetch_board_posts(board_broadcast_url, limit)
    print(f"Nikke broadcast board posts: {len(broadcast_posts)}")
    for i, p in enumerate(broadcast_posts[:3]):
        print(f"  {i+1}. {p['title'][:60]}")
    
    for p in broadcast_posts:
        # "특별" + "방송" 또는 "생방송" 키워드로 완화
        if ("특별" in p["title"] and "방송" in p["title"]) or "생방송" in p["title"]:
            print(f"Found broadcast post: {p['title']}")
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
                print(f"  No date found in body (length: {len(body)})")
    return out


def parse_ww(board_tuning_url: str, board_broadcast_url: str, limit: int = 20) -> List[Dict]:
    out: List[Dict] = []
    posts_tuning = fetch_board_posts(board_tuning_url, limit)
    print(f"WW tuning board posts: {len(posts_tuning)}")
    for i, p in enumerate(posts_tuning[:3]):
        print(f"  {i+1}. {p['title'][:60]}")
    
    posts_notice = {p["title"]: p for p in posts_tuning}
    for p in posts_tuning:
        # "캐릭터" + "이벤트" + "튜닝" 패턴 완화
        if ("캐릭터" in p["title"] and "이벤트" in p["title"] and "튜닝" in p["title"]) or \
           ("이벤트" in p["title"] and "튜닝" in p["title"]):
            print(f"Found tuning post: {p['title']}")
            body = p.get("body", "")
            start, end = kor_range(body)
            ver_match = re.search(r"(\d+(?:\.\d+)?)\s*버전", p["title"] + " " + body)
            ver = ver_match.group(1) if ver_match else ""
            if not start and "업데이트 이후" in body and ver:
                # 버전 업데이트 점검 사전 공지에서 시작일 찾기
                for t, post in posts_notice.items():
                    if "업데이트 점검 사전 공지" in t and ver in t:
                        s_iso, _ = kor_dt(post.get("body", ""))
                        if s_iso:
                            start = s_iso.split("T")[0]
                            break
            if start and end:
                out.append({
                    "game_id": "ww",
                    "version": ver,
                    "update_date": start,
                    "end_date": end,
                    "description": f"시작일 : {int(start[5:7])}/{int(start[8:10])}\n종료일 : {int(end[5:7])}/{int(end[8:10])}\n[이벤트] 캐릭터 이벤트 튜닝",
                    "url": p["url"],
                })
            else:
                print(f"  No date range found (start={start}, end={end})")

    # 프리뷰 특별 방송 (패턴 완화)
    broadcast_posts = fetch_board_posts(board_broadcast_url, limit)
    print(f"WW broadcast board posts: {len(broadcast_posts)}")
    for i, p in enumerate(broadcast_posts[:3]):
        print(f"  {i+1}. {p['title'][:60]}")
    
    for p in broadcast_posts:
        # "프리뷰" + "방송" 또는 "특별" + "방송" 키워드로 완화
        if ("프리뷰" in p["title"] and "방송" in p["title"]) or \
           ("특별" in p["title"] and "방송" in p["title"]):
            print(f"Found broadcast post: {p['title']}")
            dt_iso, _ = kor_dt(p.get("body", ""))
            if dt_iso:
                out.append({
                    "game_id": "ww",
                    "version": "",
                    "update_date": dt_iso,
                    "description": "프리뷰 특별 방송",
                    "url": p["url"],
                })
            else:
                print(f"  No date found in body (length: {len(p.get('body', ''))})")
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


