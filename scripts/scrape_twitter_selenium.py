#!/usr/bin/env python3
"""
X(트위터) Selenium을 통한 게임 업데이트 스크래핑
한국 공식 계정의 최신 트윗 수집
"""
import sys
import io
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 공식 계정
ACCOUNTS = {
    "star_rail": "honkaisr_kr",  # 붕괴: 스타레일 한국 공식
    "zzz": "ZZZ_KO",  # 젠레스 존 제로 한국 공식
}

# 키워드 감지
KEYWORDS = {
    "star_rail": ["워프", "이벤트 워프", "픽업", "확률 UP", "출시", "키레네", "룬메이"],
    "zzz": ["채널", "기간 한정", "픽업", "확률 UP", "출시", "다이아린", "Lighter"],
}

def get_selenium_driver():
    """Selenium 드라이버 생성"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_tweets(account: str, driver) -> List[Dict]:
    """계정에서 최신 트윗 가져오기"""
    url = f"https://x.com/{account}"
    print(f"\nFetching: {url}")
    
    try:
        driver.get(url)
        time.sleep(5)  # 페이지 로드 대기
        
        # 스크롤하여 더 많은 트윗 로드
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # 트윗 요소 찾기
        # X(트위터)의 구조가 자주 바뀌므로 여러 선택자 시도
        tweet_selectors = [
            "article[data-testid='tweet']",
            "div[data-testid='tweet']",
            "article",
        ]
        
        tweets = []
        for selector in tweet_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"  ✅ Found {len(elements)} tweets using selector: {selector}")
                
                for elem in elements[:20]:  # 최근 20개만
                    try:
                        text = elem.text
                        if text:
                            # 링크 추출
                            links = elem.find_elements(By.TAG_NAME, "a")
                            tweet_url = ""
                            for link in links:
                                href = link.get_attribute("href")
                                if href and "/status/" in href:
                                    tweet_url = href
                                    break
                            
                            tweets.append({
                                "text": text,
                                "url": tweet_url,
                            })
                    except Exception as e:
                        continue
                
                break
        
        if not tweets:
            print(f"  ⚠️  No tweets found")
        
        return tweets
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

def extract_date_from_tweet(text: str) -> Tuple[str, str]:
    """트윗에서 날짜 범위 추출"""
    # 패턴 1: MM/DD ~ MM/DD
    m = re.search(r"(\d{1,2})/(\d{1,2})\s*[~\-–—]\s*(\d{1,2})/(\d{1,2})", text)
    if m:
        year = datetime.now().year
        start = f"{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        end = f"{year}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
        return start, end
    
    # 패턴 2: YYYY/MM/DD ~ YYYY/MM/DD
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})\s*[~\-–—]\s*(\d{4})/(\d{1,2})/(\d{1,2})", text)
    if m:
        start = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        end = f"{m.group(4)}-{int(m.group(5)):02d}-{int(m.group(6)):02d}"
        return start, end
    
    # 패턴 3: X월 X일 ~ X월 X일
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*[~\-–—]\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if m:
        year = datetime.now().year
        start = f"{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        end = f"{year}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
        return start, end
    
    return "", ""

def parse_tweets(game_id: str, tweets: List[Dict]) -> List[Dict]:
    """트윗에서 업데이트 정보 파싱"""
    updates = []
    keywords = KEYWORDS.get(game_id, [])
    
    for tweet in tweets:
        text = tweet["text"]
        url = tweet["url"]
        
        # 키워드 매칭
        if not any(kw in text for kw in keywords):
            continue
        
        print(f"\n🔍 키워드 감지:")
        print(f"   {text[:100]}...")
        
        # 날짜 추출
        start_date, end_date = extract_date_from_tweet(text)
        
        if not start_date:
            print(f"  ⚠️  날짜 추출 실패")
            continue
        
        # 제목 추출 (첫 줄)
        title_lines = text.split('\n')
        title = title_lines[0] if title_lines else text[:60]
        
        update = {
            "game_id": game_id,
            "version": "",
            "update_date": start_date,
            "description": title,
            "url": url or f"https://x.com/{ACCOUNTS[game_id]}",
        }
        
        if end_date:
            update["end_date"] = end_date
        
        updates.append(update)
        print(f"  ✅ 추가: {start_date} ~ {end_date or 'N/A'} - {title[:40]}")
    
    return updates

def main():
    print("=" * 60)
    print("X(트위터) Selenium 스크래퍼")
    print("=" * 60)
    
    driver = get_selenium_driver()
    all_updates = []
    
    try:
        # 각 게임별로 스크래핑
        for game_id, account in ACCOUNTS.items():
            print(f"\n### {game_id.upper()} (@{account}) ###")
            
            tweets = fetch_tweets(account, driver)
            
            if not tweets:
                print(f"  ⚠️  트윗을 가져올 수 없습니다")
                continue
            
            # 트윗 파싱
            updates = parse_tweets(game_id, tweets)
            all_updates.extend(updates)
            print(f"  📊 총 {len(updates)}개 업데이트 감지")
    
    finally:
        driver.quit()
    
    # 기존 데이터와 병합
    print("\n" + "=" * 60)
    print("기존 데이터와 병합")
    print("=" * 60)
    
    try:
        with open('data/updates.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []
    
    print(f"기존 업데이트 수: {len(existing_data)}")
    print(f"새로운 업데이트 수: {len(all_updates)}")
    
    # 중복 제거
    def key(u):
        return f"{u.get('game_id')}|{u.get('update_date')}|{u.get('description','')[:40]}"
    
    existing_keys = {key(u) for u in existing_data}
    added = 0
    
    for update in all_updates:
        if key(update) not in existing_keys:
            existing_data.append(update)
            added += 1
            print(f"  ✅ 추가: {update['game_id']} - {update['description'][:50]}")
    
    if added > 0:
        with open('data/updates.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ {added}개 새 업데이트 추가 완료!")
    else:
        print(f"\nℹ️  새로운 업데이트 없음")
    
    print(f"최종 업데이트 수: {len(existing_data)}")

if __name__ == "__main__":
    main()

