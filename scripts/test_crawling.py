#!/usr/bin/env python3
"""
크롤링 테스트 스크립트 - 문제점 빠른 진단
"""

import requests
from bs4 import BeautifulSoup

def test_requests_crawling():
    """requests로 기본 크롤링 테스트"""
    print("=== requests 기반 크롤링 테스트 ===")
    
    # 니케 업데이트 게시판
    nikke_url = "https://game.naver.com/lounge/nikke/board/48"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
    
    try:
        print(f"니케 게시판 접근: {nikke_url}")
        r = requests.get(nikke_url, headers=headers, timeout=30)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # 게시글 제목 링크 찾기
        title_links = soup.find_all("a", class_=lambda x: x and "post_board_title" in x)
        print(f"찾은 게시글 수: {len(title_links)}")
        
        # 상위 3개 게시글 제목 출력
        for i, link in enumerate(title_links[:3]):
            title = link.get_text(strip=True)
            href = link.get("href")
            print(f"  {i+1}. {title[:50]}...")
            print(f"     URL: {href}")
            
            # 특수모집 관련 키워드 체크
            if any(keyword in title for keyword in ['특수모집', '합류', '모집']):
                print(f"     *** 모집 관련 키워드 발견! ***")
        
        print("니케 크롤링 성공!")
        
    except Exception as e:
        print(f"니케 크롤링 실패: {e}")
    
    print()
    
    # 명조 게시판
    ww_url = "https://game.naver.com/lounge/WutheringWaves/board/28"
    
    try:
        print(f"명조 게시판 접근: {ww_url}")
        r = requests.get(ww_url, headers=headers, timeout=30)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # 게시글 제목 링크 찾기
        title_links = soup.find_all("a", class_=lambda x: x and "post_board_title" in x)
        print(f"찾은 게시글 수: {len(title_links)}")
        
        # 상위 3개 게시글 제목 출력
        for i, link in enumerate(title_links[:3]):
            title = link.get_text(strip=True)
            href = link.get("href")
            print(f"  {i+1}. {title[:50]}...")
            print(f"     URL: {href}")
            
            # 캐릭터 이벤트 튜닝 관련 키워드 체크
            if any(keyword in title for keyword in ['캐릭터', '이벤트', '튜닝']):
                print(f"     *** 캐릭터 이벤트 튜닝 발견! ***")
        
        print("명조 크롤링 성공!")
        
    except Exception as e:
        print(f"명조 크롤링 실패: {e}")

if __name__ == "__main__":
    test_requests_crawling()


