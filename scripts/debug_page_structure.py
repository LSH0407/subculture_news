#!/usr/bin/env python3
"""
페이지 구조 디버깅 스크립트
"""

import requests
from bs4 import BeautifulSoup

def debug_page_structure():
    """페이지 구조 분석"""
    print("=== 페이지 구조 디버깅 ===")
    
    nikke_url = "https://game.naver.com/lounge/nikke/board/48"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
    
    try:
        print(f"니케 게시판 접근: {nikke_url}")
        r = requests.get(nikke_url, headers=headers, timeout=30)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        print(f"페이지 크기: {len(r.text)} 문자")
        print(f"HTML 구조 미리보기:")
        print(r.text[:1000])
        print("...")
        print(r.text[-500:])
        
        # 다양한 선택자로 링크 찾기 시도
        selectors_to_try = [
            "a[class*='post_board_title']",
            "a[class*='title']", 
            "a[href*='detail']",
            ".post_board_title",
            "[class*='post']",
            "[class*='title']",
            "a"
        ]
        
        for selector in selectors_to_try:
            elements = soup.select(selector)
            print(f"\n선택자 '{selector}': {len(elements)}개 요소 발견")
            if elements:
                for i, elem in enumerate(elements[:3]):
                    print(f"  {i+1}. {elem.get_text(strip=True)[:50]}...")
                    if elem.get("href"):
                        print(f"      href: {elem.get('href')}")
                    if elem.get("class"):
                        print(f"      class: {elem.get('class')}")
        
    except Exception as e:
        print(f"디버깅 실패: {e}")

if __name__ == "__main__":
    debug_page_structure()


