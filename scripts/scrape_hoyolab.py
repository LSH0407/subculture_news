#!/usr/bin/env python3
"""
HoYoLAB Selenium 기반 스크래퍼 (기존 스크래퍼 교체)
동적 로딩 문제 해결을 위해 Selenium 사용
"""

import json
import os
import re
import sys
import io
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass


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
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def fetch_posts(author_id: str, limit: int = 20) -> List[Dict]:
    """Selenium을 사용하여 HoYoLAB 포스트 가져오기"""
    driver = setup_driver()
    posts = []
    
    try:
        url = f"{BASE}/accountCenter/postList?id={author_id}"
        print(f"Fetching from: {url}")
        driver.get(url)
        
        # 페이지 로딩 대기 (더 긴 시간)
        wait = WebDriverWait(driver, 20)
        
        # 포스트 링크들이 로드될 때까지 대기
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/article/']")))
            # 추가 대기: 동적 콘텐츠 로딩
            import time
            time.sleep(3)
            
            # 페이지를 스크롤하여 더 많은 콘텐츠 로딩
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
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
                
                # 페이지 로딩 대기 (동적 콘텐츠)
                import time
                time.sleep(3)
                
                # 제목이 비어있거나 짧으면 페이지에서 다시 찾기
                if not post["title"] or len(post["title"]) < 10:
                    try:
                        # h1 태그가 로드될 때까지 더 긴 시간 대기
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                        time.sleep(2)  # 추가 대기
                        
                        title_element = driver.find_element(By.TAG_NAME, "h1")
                        new_title = title_element.text.strip()
                        if new_title:
                            post["title"] = new_title
                            try:
                                print(f"  -> 제목 업데이트: {new_title[:50]}")
                            except:
                                print(f"  -> 제목 업데이트 완료")
                    except Exception as e:
                        print(f"  -> 제목 업데이트 실패: {e}")
                
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
    """Return (iso_datetime_kst, human_md) from strings like '8월 22일 20:30(KST)'.
    If time missing, returns date only ISO (YYYY-MM-DD)."""
    # ex: 2025/12/17 06:00 (UTC+8) - 슬래시 형식 (시간 포함, UTC+8)
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})\s*[\(（]?\s*UTC\+8\s*[\)）]?", text)
    if m:
        y, mm, dd, hh, mi = map(int, m.groups())
        # UTC+8을 KST(UTC+9)로 변환 (+1시간)
        dt = datetime(y, mm, dd, hh, mi)
        return dt.strftime("%Y-%m-%d"), f"{mm}/{dd}"
    # ex: 2025/12/17 06:00 (서버 시간) - 슬래시 형식 (시간 포함)
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})", text)
    if m:
        y, mm, dd, hh, mi = map(int, m.groups())
        dt = datetime(y, mm, dd, hh, mi)
        return dt.strftime("%Y-%m-%d"), f"{mm}/{dd}"
    # ex: 8월 22일 20:30(KST) 또는 8월 22일 20:30（KST） - 전각 콜론, 전각 공백, KST 변형 모두 지원
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*(\d{1,2})[:：]\s*(\d{2})\s*[\(（]?\s*KST\s*[\)）]?", text)
    if m:
        mm, dd, hh, mi = map(int, m.groups())
        year = datetime.now().year
        dt = datetime(year, mm, dd, hh, mi)
        return dt.strftime("%Y-%m-%dT%H:%M:00+09:00"), f"{mm}/{dd} {hh:02d}:{mi:02d}"
    # ex: 8월 22일 (시간 미포함)
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if m:
        mm, dd = map(int, m.groups())
        year = datetime.now().year
        dt = datetime(year, mm, dd)
        return dt.strftime("%Y-%m-%d"), f"{mm}/{dd}"
    return "", ""


def find_korean_daterange(text: str) -> Tuple[str, str]:
    """Parse a range like '9월 24일 ~ 10월 15일' or '2025/11/26 12:00 ~ 2025/12/16 15:00' -> (YYYY-MM-DD, YYYY-MM-DD)."""
    # 패턴 -1: "업데이트 후 ~ YYYY/MM/DD HH:MM" (종료일만 명시, 시작일은 없음)
    m = re.search(r"업데이트\s*(?:후|이후).*?[~\-\–—]\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+\d{1,2}:\d{2}", text)
    if m:
        y, mm, dd = map(int, m.groups())
        # 시작일은 반환하지 않고 종료일만 반환 (빈 문자열, 종료일)
        return "", datetime(y, mm, dd).strftime("%Y-%m-%d")
    
    # 패턴 00: "YYYY/MM/DD HH:MM ~ YYYY/MM/DD HH:MM" (슬래시 형식, 시간 포함)
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})\s+\d{1,2}:\d{2}\s*[~\-\–—]\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+\d{1,2}:\d{2}", text)
    if m:
        y1, mm1, dd1, y2, mm2, dd2 = map(int, m.groups())
        return datetime(y1, mm1, dd1).strftime("%Y-%m-%d"), datetime(y2, mm2, dd2).strftime("%Y-%m-%d")
    
    # 패턴 0: "YYYY년 X월 X일 HH:MM ~ YYYY년 X월 X일 HH:MM" (시간 포함, 연도 있음)
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*\d{1,2}:\d{2}\s*[~\-\–—]\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*\d{1,2}:\d{2}", text)
    if m:
        y1, mm1, dd1, y2, mm2, dd2 = map(int, m.groups())
        return datetime(y1, mm1, dd1).strftime("%Y-%m-%d"), datetime(y2, mm2, dd2).strftime("%Y-%m-%d")
    
    # 패턴 1: "YYYY년 X월 X일 ~ YYYY년 X월 X일" (연도 있음)
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*[~\-\–—]\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", text)
    if m:
        y1, mm1, dd1, y2, mm2, dd2 = map(int, m.groups())
        return datetime(y1, mm1, dd1).strftime("%Y-%m-%d"), datetime(y2, mm2, dd2).strftime("%Y-%m-%d")
    
    # 패턴 2: "X월 X일부터 X월 X일까지"
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*부터.*?(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*까지", text)
    if not m:
        # 패턴 3: "X월 X일 ~ X월 X일" (일반 형태)
        m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*[~\-\–—]\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if not m:
        return "", ""
    y = datetime.now().year
    mm1, dd1, mm2, dd2 = map(int, m.groups())
    # 연도 넘어가는 경우 처리 (예: 12월 -> 1월)
    y2 = y if mm2 >= mm1 else y + 1
    return datetime(y, mm1, dd1).strftime("%Y-%m-%d"), datetime(y2, mm2, dd2).strftime("%Y-%m-%d")


def extract_version(text: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)?)\s*버전", text)
    return m.group(1) if m else ""


def build_desc(start_md: str, end_md: str, lines: List[str]) -> str:
    out = [f"시작일 : {start_md}", f"종료일 : {end_md}"] if start_md and end_md else []
    out.extend(lines)
    return "\n".join(out)


def parse_zzz(posts: List[Dict]) -> List[Dict]:
    results: List[Dict] = []
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
        
        # 특별 방송: 더 유연한 감지 로직
        # 1. "특별 방송" 키워드 체크 (띄어쓰기 무시)
        # 2. "방송 예고" 키워드 체크
        # 3. "버전" + "방송" 조합
        is_broadcast = (
            ("특별" in title and "방송" in title) or
            ("특별" in body and "방송" in body) or
            ("방송" in title and "예고" in title) or
            ("방송" in body and "예고" in body) or
            (ver and "방송" in title) or
            (ver and "방송" in body)
        )
        
        if is_broadcast:
            print(f"  -> 특별 방송 후보 발견: {title[:50] if title else '(제목 없음)'}...")
            # 본문에서 시간 포함 형태 우선, 없으면 제목에서 재시도
            dt_iso, md = find_korean_datetime(body)
            if not dt_iso:
                dt_iso, md = find_korean_datetime(title)
            if dt_iso:
                # 설명 구성 (버전 정보 포함)
                if ver:
                    desc = f"{ver} 버전 특별 방송"
                elif "예고" in title or "예고" in body:
                    desc = "특별 방송 예고"
                else:
                    desc = "특별 방송"
                
                result = {
                    "game_id": "zzz",
                    "version": ver or "",
                    "update_date": dt_iso,
                    "description": desc,
                    "url": url,
                }
                results.append(result)
                print(f"  -> 특별 방송 파싱 성공: {result}")
            else:
                print(f"  -> 특별 방송 날짜 파싱 실패 (title: '{title[:50] if title else '(없음)'}', body length: {len(body)})")
            continue
        # 기간 한정 채널 (다양한 패턴 지원)
        if "기간 한정 채널" in title or ("채널" in title and ver):
            print(f"  -> 기간 한정 채널 후보 발견: {title[:50]}")
            print(f"     본문 샘플: {body[:200]}")
            
            # 캐릭터명 추출 (「캐릭터명」 패턴)
            char_names = re.findall(r"「([^」]+)」", title)
            char_desc = " / ".join(char_names) if char_names else "기간 한정 채널"
            
            # 상/하 구분
            phase = ""
            start, end = "", ""
            
            if "상)" in title or "(상" in title or "상반기" in title:
                phase = "(상)"
                print(f"     -> 상반기 채널 감지")
                # 본문에서 날짜 범위 추출 시도
                start_parsed, end_parsed = find_korean_daterange(body)
                # "업데이트 후 ~ 종료일" 형태면 start_parsed가 비어있음
                if not start_parsed and end_parsed:
                    # 캐시된 업데이트 날짜 사용
                    start = version_to_update_date.get(ver, "")
                    end = end_parsed
                    print(f"     -> 시작일: 캐시({start}), 종료일: 본문({end})")
                elif start_parsed and end_parsed:
                    # 본문에 명확한 시작일과 종료일이 있는 경우
                    start, end = start_parsed, end_parsed
                    print(f"     -> 시작일/종료일 모두 본문에서 추출: {start} ~ {end}")
                else:
                    # 종료일만 추출 (본문에서)
                    start = version_to_update_date.get(ver, "")
                    _, end = find_korean_daterange(body)
                    print(f"     -> 시작일: 캐시({start}), 종료일: 본문({end})")
                    
            elif "하)" in title or "(하" in title or "하반기" in title:
                phase = "(하)"
                print(f"     -> 하반기 채널 감지")
                start, end = find_korean_daterange(body)
                print(f"     -> 본문에서 추출: {start} ~ {end}")
            else:
                # 상/하 구분 없는 경우
                print(f"     -> 일반 채널 (상/하 구분 없음)")
                start, end = find_korean_daterange(body)
                if not start:
                    start = version_to_update_date.get(ver, "")
                    print(f"     -> 시작일 캐시 사용: {start}")
                print(f"     -> 날짜: {start} ~ {end}")
            
            if start and end:
                md_s = start.replace("2025-", "").replace("2024-", "").replace("2026-", "")
                md_e = end.replace("2025-", "").replace("2024-", "").replace("2026-", "")
                desc = build_desc(md_s, md_e, [f"[이벤트] {char_desc}{phase}"])
                results.append({
                    "game_id": "zzz",
                    "version": ver,
                    "update_date": start,
                    "end_date": end,
                    "description": desc,
                    "url": url,
                })
                print(f"    ✅ 채널 파싱 성공: {start} ~ {end}, {char_desc}{phase}")
            else:
                print(f"    ❌ 날짜 파싱 실패 (start={start}, end={end})")
    return results


def parse_star_rail(posts: List[Dict]) -> List[Dict]:
    results: List[Dict] = []
    version_to_update_date: Dict[str, str] = {}
    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        ver = extract_version(title + " " + body)
        # 업데이트 점검 예고 또는 업데이트 안내에서 시작일 캐싱
        if ("업데이트 점검 예고" in title or "업데이트 안내" in title) and ver:
            dt_iso, _ = find_korean_datetime(body)
            if not dt_iso:
                dt_iso, _ = find_korean_datetime(title)
            if dt_iso:
                version_to_update_date[ver] = dt_iso.split("T")[0]

    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        url = p["url"]
        ver = extract_version(title + " " + body)
        
        # 프리뷰 스페셜 프로그램
        if "프리뷰 스페셜 프로그램" in title and ver:
            dt_iso, _ = find_korean_datetime(body)
            if not dt_iso:
                dt_iso, _ = find_korean_datetime(title)
            if dt_iso:
                results.append({
                    "game_id": "star_rail",
                    "version": ver,
                    "update_date": dt_iso,
                    "description": f"{ver} 버전 프리뷰 스페셜 프로그램",
                    "url": url,
                })
                print(f"  -> 프리뷰 스페셜 프로그램 파싱: {ver}")
            continue
        
        # 이벤트 워프 (1/2) - 기존 로직
        m = re.search(r"이벤트\s*워프\s*\((\d)\)", title)
        if m and ver:
            y = m.group(1)
            print(f"  -> 이벤트 워프 발견: {ver} 버전, 페이즈 {y}")
            if y == "1":
                # 시작일: version_to_update_date에서 가져오거나, 본문에서 직접 추출
                start = version_to_update_date.get(ver, "")
                _, end = find_korean_daterange(body)
                
                # 시작일이 없으면 본문에서 "YYYY/MM/DD X.X 버전 업데이트 후" 패턴으로 추출
                if not start:
                    # "이벤트 워프 기간은 YYYY/MM/DD X.X 버전 업데이트 후" 패턴 먼저 시도
                    start_match = re.search(r"이벤트\s*워프\s*기간[은는]?\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+\d+\.\d+\s*버전\s*업데이트\s*후", body)
                    if not start_match:
                        # "YYYY/MM/DD X.X 버전 업데이트 후" 패턴
                        start_match = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})\s+\d+\.\d+\s*버전\s*업데이트\s*후", body)
                    if start_match:
                        y1, mm1, dd1 = map(int, start_match.groups())
                        start = datetime(y1, mm1, dd1).strftime("%Y-%m-%d")
                        print(f"    -> 본문에서 시작일 추출: {start}")
                
                if start and end:
                    md_s = start.split("-")
                    md_e = end.split("-")
                    
                    # 본문에서 캐릭터명 추출
                    char_names = re.findall(r"「([^」]+)\(", body)
                    if char_names:
                        # 중복 제거하고 최대 2개
                        unique_chars = list(dict.fromkeys(char_names))[:2]
                        char_desc = " / ".join(unique_chars)
                        desc = build_desc(f"{int(md_s[1])}/{int(md_s[2])}", f"{int(md_e[1])}/{int(md_e[2])}", [f"[이벤트] {char_desc}"])
                    else:
                        desc = build_desc(f"{int(md_s[1])}/{int(md_s[2])}", f"{int(md_e[1])}/{int(md_e[2])}", ["[이벤트] 워프(1)"])
                    
                    results.append({
                        "game_id": "star_rail",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": desc,
                        "url": url,
                    })
                    print(f"    -> 워프(1) 파싱 성공: {start} ~ {end}")
                else:
                    print(f"    -> 워프(1) 파싱 실패: start={start}, end={end}")
            else:
                start, end = find_korean_daterange(body)
                if start and end:
                    md_s = start.split("-")
                    md_e = end.split("-")
                    
                    # 본문에서 캐릭터명 추출
                    char_names = re.findall(r"「([^」]+)\(", body)
                    if char_names:
                        unique_chars = list(dict.fromkeys(char_names))[:2]
                        char_desc = " / ".join(unique_chars)
                        desc = build_desc(f"{int(md_s[1])}/{int(md_s[2])}", f"{int(md_e[1])}/{int(md_e[2])}", [f"[이벤트] {char_desc}"])
                    else:
                        desc = build_desc(f"{int(md_s[1])}/{int(md_s[2])}", f"{int(md_e[1])}/{int(md_e[2])}", ["[이벤트] 워프(2)"])
                    
                    results.append({
                        "game_id": "star_rail",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": desc,
                        "url": url,
                    })
                    print(f"    -> 워프(2) 파싱 성공: {start} ~ {end}")
            continue
        
        # 새로운 패턴: "워프" 키워드가 있는 게시글 (캐릭터 이름 포함)
        if "워프" in title and ver:
            print(f"  -> 워프 관련 게시글 발견: {title[:50]}")
            # 날짜 범위 추출
            start, end = find_korean_daterange(body)
            if start and end:
                # 캐릭터명 추출 시도
                char_names = re.findall(r"「([^」]+)」", title)
                if char_names:
                    char_desc = " / ".join(char_names)
                else:
                    char_desc = "이벤트 워프"
                
                md_s = start.split("-")
                md_e = end.split("-")
                desc = build_desc(f"{int(md_s[1])}/{int(md_s[2])}", f"{int(md_e[1])}/{int(md_e[2])}", [f"[이벤트] {char_desc}"])
                results.append({
                    "game_id": "star_rail",
                    "version": ver,
                    "update_date": start,
                    "end_date": end,
                    "description": desc,
                    "url": url,
                })
                print(f"    -> 워프 파싱 성공: {start} ~ {end}")
    return results


def merge_updates(new_updates: List[Dict]) -> None:
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
    print(f"HoYoLAB merged: +{added} items")


def main():
    zzz_id = os.getenv("HOYOLAB_ZZZ_AUTHOR", "219270333")
    sr_id = os.getenv("HOYOLAB_SR_AUTHOR", "172534910")
    limit = int(os.getenv("HOYOLAB_LIMIT", "20"))

    all_updates: List[Dict] = []

    # ZZZ 스크래핑
    try:
        print("=== ZZZ HoYoLAB Selenium 스크래핑 시작 ===")
        zzz_posts = fetch_posts(zzz_id, limit=limit)
        print(f"ZZZ: 총 {len(zzz_posts)}개 포스트 수집")
        
        zzz_updates = parse_zzz(zzz_posts)
        all_updates += zzz_updates
        print(f"ZZZ: {len(zzz_updates)}개 업데이트 파싱")
        
    except Exception as e:
        print(f"ZZZ Selenium scrape failed: {e}")

    # 스타레일 스크래핑
    try:
        print("=== Star Rail HoYoLAB Selenium 스크래핑 시작 ===")
        sr_posts = fetch_posts(sr_id, limit=limit)
        print(f"Star Rail: 총 {len(sr_posts)}개 포스트 수집")
        
        sr_updates = parse_star_rail(sr_posts)
        all_updates += sr_updates
        print(f"Star Rail: {len(sr_updates)}개 업데이트 파싱")
        
    except Exception as e:
        print(f"Star Rail Selenium scrape failed: {e}")

    print(f"=== 총 {len(all_updates)}개 업데이트 병합 ===")
    merge_updates(all_updates)


if __name__ == "__main__":
    main()


