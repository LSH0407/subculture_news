#!/usr/bin/env python3
"""
X(트위터) RSS 피드를 통한 게임 업데이트 스크래핑
Nitter 인스턴스를 사용하여 API 키 없이 트윗 수집
"""
import sys
import io
import json
import re
from datetime import datetime
import feedparser
from typing import List, Dict, Tuple

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Nitter 인스턴스 목록 (fallback 지원)
NITTER_INSTANCES = [
    "nitter.poast.org",
    "nitter.privacydev.net",
    "nitter.net",
]

# 공식 계정
ACCOUNTS = {
    "star_rail": "honkaisr_kr",  # 붕괴: 스타레일 한국 공식
    "zzz": "ZZZ_KO",  # 젠레스 존 제로 한국 공식
}

# 키워드 감지
KEYWORDS = {
    "star_rail": ["워프", "이벤트 워프", "픽업", "확률 UP", "출시"],
    "zzz": ["채널", "기간 한정", "픽업", "확률 UP", "출시"],
}

def fetch_tweets(account: str, instance: str) -> List[Dict]:
    """RSS 피드에서 트윗 가져오기"""
    feed_url = f"https://{instance}/{account}/rss"
    print(f"Fetching: {feed_url}")
    
    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print(f"  ⚠️  No entries found")
            return []
        
        print(f"  ✅ Found {len(feed.entries)} tweets")
        
        tweets = []
        for entry in feed.entries:
            tweets.append({
                "title": entry.get("title", ""),
                "description": entry.get("description", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "published_parsed": entry.get("published_parsed"),
            })
        
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
        title = tweet["title"]
        desc = tweet["description"]
        full_text = f"{title}\n{desc}"
        
        # 키워드 매칭
        if not any(kw in full_text for kw in keywords):
            continue
        
        print(f"\n🔍 키워드 감지: {title[:60]}")
        
        # 날짜 추출
        start_date, end_date = extract_date_from_tweet(full_text)
        
        if not start_date:
            # 게시 날짜 사용
            if tweet["published_parsed"]:
                pub_time = tweet["published_parsed"]
                start_date = f"{pub_time.tm_year}-{pub_time.tm_mon:02d}-{pub_time.tm_mday:02d}"
                print(f"  ℹ️  날짜 추출 실패, 게시 날짜 사용: {start_date}")
        
        if start_date:
            update = {
                "game_id": game_id,
                "version": "",  # 버전은 별도 파싱 필요
                "update_date": start_date,
                "description": title,
                "url": tweet["link"],
            }
            
            if end_date:
                update["end_date"] = end_date
            
            updates.append(update)
            print(f"  ✅ 추가: {start_date} ~ {end_date or 'N/A'}")
    
    return updates

def main():
    print("=" * 60)
    print("X(트위터) RSS 피드 스크래퍼")
    print("=" * 60)
    
    all_updates = []
    
    # 각 게임별로 스크래핑
    for game_id, account in ACCOUNTS.items():
        print(f"\n### {game_id.upper()} (@{account}) ###")
        
        tweets = None
        # Nitter 인스턴스 fallback
        for instance in NITTER_INSTANCES:
            tweets = fetch_tweets(account, instance)
            if tweets:
                break
        
        if not tweets:
            print(f"  ⚠️  모든 Nitter 인스턴스에서 실패")
            continue
        
        # 트윗 파싱
        updates = parse_tweets(game_id, tweets)
        all_updates.extend(updates)
        print(f"  📊 총 {len(updates)}개 업데이트 감지")
    
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
        print(f"\n✅ 새로운 업데이트 없음")
    
    print(f"최종 업데이트 수: {len(existing_data)}")

if __name__ == "__main__":
    main()

