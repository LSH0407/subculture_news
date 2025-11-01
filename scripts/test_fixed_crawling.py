#!/usr/bin/env python3
"""
수정된 크롤링 테스트
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from scrape_lounge import fetch_board_posts

def test_fixed_crawling():
    """수정된 크롤링 테스트"""
    print("=== 수정된 크롤링 테스트 ===")
    
    # 니케 업데이트 게시판 (소수만 테스트)
    nikke_url = "https://game.naver.com/lounge/nikke/board/48"
    
    try:
        print("니케 게시판 크롤링 테스트...")
        posts = fetch_board_posts(nikke_url, max_items=5)  # 5개만 테스트
        
        print(f"\n=== 결과: {len(posts)}개 게시글 수집 ===")
        for i, post in enumerate(posts):
            print(f"{i+1}. {post['title'][:50]}...")
            print(f"   URL: {post['url']}")
            
            # 특수모집 관련 키워드 체크
            title = post['title']
            body = post.get('body', '')
            
            if any(keyword in title for keyword in ['특수모집', '합류', '모집']):
                print(f"   *** 제목에서 모집 키워드 발견! ***")
            
            if any(keyword in body for keyword in ['특수모집', '합류', '모집에 합류']):
                print(f"   *** 본문에서 모집 키워드 발견! ***")
            
            print()
        
    except Exception as e:
        print(f"테스트 실패: {e}")

if __name__ == "__main__":
    test_fixed_crawling()


