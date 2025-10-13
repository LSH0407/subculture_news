#!/usr/bin/env python3
"""
HoYoLAB Selenium 기반 스크래퍼
동적 로딩 문제 해결을 위해 Selenium 사용
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


BASE = "https://www.hoyolab.com"


def setup_driver():
    """Chrome WebDriver 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 헤드리스 모드
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (compatible; subculture-news/1.0)")
    # GitHub Actions 환경을 위한 추가 옵션
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"WebDriver Manager failed, trying default: {e}")
        driver = webdriver.Chrome(options=chrome_options)
    
    return driver


def fetch_posts_selenium(author_id: str, limit: int = 20) -> List[Dict]:
    """Selenium을 사용하여 HoYoLAB 포스트 가져오기"""
    driver = setup_driver()
    posts = []
    
    try:
        url = f"{BASE}/accountCenter/postList?id={author_id}"
        print(f"Fetching from: {url}")
        driver.get(url)
        
        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 10)
        
        # 포스트 링크들이 로드될 때까지 대기
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/article/']")))
        except TimeoutException:
            print("포스트 링크를 찾을 수 없습니다. 페이지 구조를 확인합니다...")
            # 페이지 소스 확인
            page_source = driver.page_source
            if "Loading" in page_source and len(page_source) < 1000:
                print("페이지가 여전히 로딩 중입니다.")
                return posts
            else:
                print("페이지는 로드되었지만 예상된 구조가 아닙니다.")
        
        # 포스트 링크들 찾기
        post_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/article/']")
        print(f"Found {len(post_links)} post links")
        
        seen_urls = set()
        for i, link in enumerate(post_links[:limit]):
            try:
                title = link.text.strip()
                href = link.get_attribute("href")
                
                # 제목이 비어있으면 부모 요소에서 찾기
                if not title:
                    try:
                        parent = link.find_element(By.XPATH, "./..")
                        title = parent.text.strip()
                    except:
                        pass
                
                # 여전히 비어있으면 다른 방법으로 찾기
                if not title:
                    try:
                        # 링크 주변의 텍스트 요소들 찾기
                        title_elements = driver.find_elements(By.XPATH, f"//a[@href='{href}']/following-sibling::* | //a[@href='{href}']/preceding-sibling::*")
                        for elem in title_elements:
                            if elem.text.strip():
                                title = elem.text.strip()
                                break
                    except:
                        pass
                
                print(f"링크 {i+1}: title='{title}', href='{href}'")
                
                if not href:
                    print(f"  -> URL이 비어있음, 건너뜀")
                    continue
                
                # reply 파라미터가 있는 URL은 제외
                if "?reply=" in href:
                    print(f"  -> 댓글 링크, 건너뜀")
                    continue
                
                if href in seen_urls:
                    print(f"  -> 중복 URL, 건너뜀")
                    continue
                    
                seen_urls.add(href)
                posts.append({"title": title or "", "url": href})
                print(f"  -> 추가됨: {title or '(제목 없음)'}")
                
                # 특별 방송 관련 키워드 체크
                if "특별 방송" in title:
                    print(f"   *** 특별 방송 발견! ***")
                if "방송" in title:
                    print(f"   *** 방송 관련 포스트 발견! ***")
                if "프리뷰" in title:
                    print(f"   *** 프리뷰 관련 포스트 발견! ***")
                if "버전" in title:
                    print(f"   *** 버전 관련 포스트 발견! ***")
                    
            except Exception as e:
                print(f"링크 처리 중 오류: {e}")
                continue
        
        # 각 포스트의 본문 가져오기
        for i, post in enumerate(posts):
            try:
                print(f"  -> 포스트 {i+1}/{len(posts)} 처리 중: {post['url']}")
                driver.get(post["url"])
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # 페이지 로딩을 위한 추가 대기
                time.sleep(2)
                
                # 제목이 비어있으면 페이지에서 다시 찾기 (여러 방법 시도)
                if not post["title"] or len(post["title"]) < 10:
                    try:
                        # 방법 1: h1 태그에서 찾기
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                        title_element = driver.find_element(By.TAG_NAME, "h1")
                        new_title = title_element.text.strip()
                        if new_title:
                            post["title"] = new_title
                            print(f"  -> 제목 업데이트 (h1): {new_title}")
                    except:
                        try:
                            # 방법 2: 특정 클래스나 선택자로 찾기
                            title_selectors = [
                                "[data-testid='article-title']",
                                ".article-title",
                                ".post-title", 
                                "h1[class*='title']",
                                "h2[class*='title']"
                            ]
                            for selector in title_selectors:
                                try:
                                    title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                                    new_title = title_elem.text.strip()
                                    if new_title:
                                        post["title"] = new_title
                                        print(f"  -> 제목 업데이트 ({selector}): {new_title}")
                                        break
                                except:
                                    continue
                        except:
                            pass
                
                # 특별 방송 예고 포스트 강제 처리 (41722228)
                if "41722228" in post["url"]:
                    print(f"  -> 특별 방송 예고 포스트 감지, 강제 처리")
                    try:
                        # 더 긴 대기 시간과 다양한 선택자 시도
                        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                        time.sleep(3)  # 추가 대기
                        
                        # JavaScript로 제목 추출 시도
                        title_js = driver.execute_script("""
                            var title = document.querySelector('h1');
                            if (title) return title.innerText || title.textContent;
                            
                            var titleSelectors = ['[data-testid="article-title"]', '.article-title', '.post-title'];
                            for (var i = 0; i < titleSelectors.length; i++) {
                                var elem = document.querySelector(titleSelectors[i]);
                                if (elem && elem.innerText) return elem.innerText;
                            }
                            return '';
                        """)
                        
                        if title_js and title_js.strip():
                            post["title"] = title_js.strip()
                            print(f"  -> 특별 방송 예고 제목 강제 업데이트 (JS): {title_js.strip()}")
                        else:
                            # 페이지 소스에서 직접 추출 시도
                            page_source = driver.page_source
                            title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', page_source)
                            if title_match:
                                post["title"] = title_match.group(1).strip()
                                print(f"  -> 특별 방송 예고 제목 강제 업데이트 (regex): {title_match.group(1).strip()}")
                    except Exception as e:
                        print(f"  -> 특별 방송 예고 제목 업데이트 실패: {e}")
                
                # 본문 로딩 보강: 스크롤 후 innerText 재수집
                try:
                    # 페이지 하단까지 스크롤하여 동적 콘텐츠 로딩 유도
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)  # 로딩 대기
                    
                    # innerText로 더 정확한 텍스트 추출
                    body_text = driver.execute_script("return document.body.innerText;")
                    post["body"] = body_text
                except:
                    # fallback: 기존 방식
                    body_element = driver.find_element(By.TAG_NAME, "body")
                    body_text = body_element.text
                    post["body"] = body_text
                
            except Exception as e:
                print(f"포스트 본문 가져오기 실패 {post['url']}: {e}")
                post["body"] = ""
                
    except Exception as e:
        print(f"스크래핑 중 오류 발생: {e}")
        
    finally:
        driver.quit()
    
    return posts


def find_korean_datetime(text: str) -> Tuple[str, str]:
    """한국어 날짜/시간 형식 파싱"""
    # ex: 8월 22일 20:30(KST)
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*(\d{1,2}):(\d{2})\s*\(KST\)", text)
    if m:
        mm, dd, hh, mi = map(int, m.groups())
        year = datetime.now().year
        dt = datetime(year, mm, dd, hh, mi)
        return dt.strftime("%Y-%m-%dT%H:%M:00+09:00"), f"{mm}/{dd} {hh:02d}:{mi:02d}"
    
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if m:
        mm, dd = map(int, m.groups())
        year = datetime.now().year
        dt = datetime(year, mm, dd)
        return dt.strftime("%Y-%m-%d"), f"{mm}/{dd}"
    
    return "", ""


def extract_version(text: str) -> str:
    """버전 번호 추출"""
    m = re.search(r"(\d+(?:\.\d+)?)\s*버전", text)
    return m.group(1) if m else ""


def find_korean_daterange(text: str) -> Tuple[str, str]:
    """한국어 날짜 범위 파싱"""
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*[~~\-]\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if not m:
        return "", ""
    y = datetime.now().year
    mm1, dd1, mm2, dd2 = map(int, m.groups())
    return datetime(y, mm1, dd1).strftime("%Y-%m-%d"), datetime(y, mm2, dd2).strftime("%Y-%m-%d")


def build_desc(start_md: str, end_md: str, lines: List[str]) -> str:
    """설명 텍스트 생성"""
    out = [f"시작일 : {start_md}", f"종료일 : {end_md}"] if start_md and end_md else []
    out.extend(lines)
    return "\n".join(out)


def parse_zzz_selenium(posts: List[Dict]) -> List[Dict]:
    """ZZZ 포스트 파싱 (Selenium 버전)"""
    results = []
    # 캐시: 버전→업데이트 안내에서 추출한 업데이트일
    version_to_update_date: Dict[str, str] = {}
    
    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        ver = extract_version(title + " " + body)
        # 업데이트 안내 → 시작일 캐싱
        if "업데이트 안내" in title and ver:
            dt_iso, md = find_korean_datetime(body)
            if not dt_iso:
                dt_iso, md = find_korean_datetime(title)
            if dt_iso:
                version_to_update_date[ver] = dt_iso.split("T")[0]

    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        url = p["url"]
        ver = extract_version(title + " " + body)
        
        print(f"Processing ZZZ: {title}")
        
        # 특별 방송 예고
        if "특별 방송 예고" in title:
            print(f"  -> 특별 방송 예고 발견!")
            dt_iso, md = find_korean_datetime(body)
            if not dt_iso:
                dt_iso, md = find_korean_datetime(title)
            
            if dt_iso and ver:
                results.append({
                    "game_id": "zzz",
                    "version": ver,
                    "update_date": dt_iso,
                    "description": f"{ver} 버전 특별 방송",
                    "url": url,
                })
                print(f"  -> 추가됨: {ver} 버전 특별 방송 ({dt_iso})")
            else:
                print(f"  -> 날짜 또는 버전 정보 없음")
            continue
            
        # 기간 한정 채널(상/하)
        if "기간 한정 채널" in title and ver:
            print(f"  -> 기간 한정 채널 발견!")
            if "상)" in title or "(상" in title:
                start = version_to_update_date.get(ver, "")
                _, end = find_korean_daterange(body)
                if start and end:
                    results.append({
                        "game_id": "zzz",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": build_desc(start.replace("2025-", "").replace("2024-", ""), end.replace("2025-", "").replace("2024-", ""), ["[이벤트] 기간 한정 채널(상)"]),
                        "url": url,
                    })
            elif "하)" in title or "(하" in title:
                start, end = find_korean_daterange(body)
                if start and end:
                    results.append({
                        "game_id": "zzz",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": build_desc(start.replace("2025-", "").replace("2024-", ""), end.replace("2025-", "").replace("2024-", ""), ["[이벤트] 기간 한정 채널(하)"]),
                        "url": url,
                    })
    
    return results


def parse_star_rail_selenium(posts: List[Dict]) -> List[Dict]:
    """스타레일 포스트 파싱 (Selenium 버전)"""
    results = []
    version_to_update_date: Dict[str, str] = {}
    
    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        ver = extract_version(title + " " + body)
        if "업데이트 점검 예고" in title and ver:
            dt_iso, _ = find_korean_datetime(body)
            if dt_iso:
                version_to_update_date[ver] = dt_iso.split("T")[0]

    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        url = p["url"]
        ver = extract_version(title + " " + body)
        
        print(f"Processing Star Rail: {title}")
        
        # 프리뷰 스페셜 프로그램
        if "프리뷰 스페셜 프로그램" in title and ver and "-" not in title and "|" not in title:
            print(f"  -> 프리뷰 스페셜 프로그램 발견!")
            dt_iso, _ = find_korean_datetime(body)
            if dt_iso:
                results.append({
                    "game_id": "star_rail",
                    "version": ver,
                    "update_date": dt_iso,
                    "description": f"{ver} 프리뷰 스페셜 프로그램",
                    "url": url,
                })
                print(f"  -> 추가됨: {ver} 프리뷰 스페셜 프로그램 ({dt_iso})")
            continue
            
        # 이벤트 워프 (1/2)
        m = re.search(r"이벤트\s*워프\s*\((\d)\)", title)
        if m and ver:
            print(f"  -> 이벤트 워프 발견!")
            y = m.group(1)
            if y == "1":
                start = version_to_update_date.get(ver, "")
                _, end = find_korean_daterange(body)
                if start and end:
                    md_s = start.split("-")
                    md_e = end.split("-")
                    desc = build_desc(f"{int(md_s[1])}/{int(md_s[2])}", f"{int(md_e[1])}/{int(md_e[2])}", ["[이벤트] 워프(1)"])
                    results.append({
                        "game_id": "star_rail",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": desc,
                        "url": url,
                    })
                    print(f"  -> 추가됨: 이벤트 워프(1) ({start} ~ {end})")
            else:
                start, end = find_korean_daterange(body)
                if start and end:
                    md_s = start.split("-")
                    md_e = end.split("-")
                    desc = build_desc(f"{int(md_s[1])}/{int(md_s[2])}", f"{int(md_e[1])}/{int(md_e[2])}", ["[이벤트] 워프(2)"])
                    results.append({
                        "game_id": "star_rail",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": desc,
                        "url": url,
                    })
                    print(f"  -> 추가됨: 이벤트 워프(2) ({start} ~ {end})")
    
    return results


def merge_updates(new_updates: List[Dict]) -> None:
    """업데이트 병합"""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "updates.json"))
    try:
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []

    # 디듀프 키: game_id + version + update_date + description
    def key(u: Dict) -> str:
        return f"{u.get('game_id')}|{u.get('version','')}|{u.get('update_date')}|{u.get('description','')[:40]}"

    seen = {key(u) for u in existing}
    merged = existing[:]
    added = 0
    for u in new_updates:
        if key(u) in seen:
            continue
        merged.append(u)
        added += 1

    if added:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"HoYoLAB Selenium merged: +{added} items")


def main():
    """메인 함수"""
    zzz_id = os.getenv("HOYOLAB_ZZZ_AUTHOR", "219270333")
    sr_id = os.getenv("HOYOLAB_SR_AUTHOR", "172534910")
    limit = int(os.getenv("HOYOLAB_LIMIT", "20"))

    all_updates = []

    # ZZZ 스크래핑
    try:
        print("=== ZZZ HoYoLAB Selenium 스크래핑 시작 ===")
        zzz_posts = fetch_posts_selenium(zzz_id, limit=limit)
        print(f"ZZZ: 총 {len(zzz_posts)}개 포스트 수집")
        
        zzz_updates = parse_zzz_selenium(zzz_posts)
        all_updates += zzz_updates
        print(f"ZZZ: {len(zzz_updates)}개 업데이트 파싱")
        
    except Exception as e:
        print(f"ZZZ Selenium scrape failed: {e}")

    # 스타레일 스크래핑
    try:
        print("=== Star Rail HoYoLAB Selenium 스크래핑 시작 ===")
        sr_posts = fetch_posts_selenium(sr_id, limit=limit)
        print(f"Star Rail: 총 {len(sr_posts)}개 포스트 수집")
        
        sr_updates = parse_star_rail_selenium(sr_posts)
        all_updates += sr_updates
        print(f"Star Rail: {len(sr_updates)}개 업데이트 파싱")
        
    except Exception as e:
        print(f"Star Rail Selenium scrape failed: {e}")

    print(f"=== 총 {len(all_updates)}개 업데이트 병합 ===")
    merge_updates(all_updates)


if __name__ == "__main__":
    main()
