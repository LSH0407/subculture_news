import sys
import os
import json
sys.path.append('scripts')

from scrape_lounge import fetch_board_posts, parse_nikke, parse_ww, merge

def test_lounge_scraping():
    print("=== 네이버 게임 라운지 스크래핑 로컬 테스트 ===")
    
    # 니케 업데이트 보드 테스트
    nikke_update_url = "https://game.naver.com/lounge/nikke/board/48"
    nikke_broadcast_url = "https://game.naver.com/lounge/nikke/board/11"
    
    print(f"\n1. 니케 업데이트 보드 테스트: {nikke_update_url}")
    try:
        posts = fetch_board_posts(nikke_update_url, max_items=5)
        print(f"   발견된 게시글 수: {len(posts)}")
        
        for i, post in enumerate(posts[:3]):
            print(f"   {i+1}. {post['title'][:60]}...")
            print(f"      URL: {post['url']}")
            print(f"      본문 길이: {len(post.get('body', ''))}")
            
    except Exception as e:
        print(f"   니케 업데이트 보드 테스트 실패: {e}")
    
    # 니케 방송 보드 테스트
    print(f"\n2. 니케 방송 보드 테스트: {nikke_broadcast_url}")
    try:
        posts = fetch_board_posts(nikke_broadcast_url, max_items=5)
        print(f"   발견된 게시글 수: {len(posts)}")
        
        for i, post in enumerate(posts[:3]):
            print(f"   {i+1}. {post['title'][:60]}...")
            print(f"      URL: {post['url']}")
            print(f"      본문 길이: {len(post.get('body', ''))}")
            
    except Exception as e:
        print(f"   니케 방송 보드 테스트 실패: {e}")
    
    # 명조 튜닝 보드 테스트
    ww_tuning_url = "https://game.naver.com/lounge/WutheringWaves/board/28"
    ww_broadcast_url = "https://game.naver.com/lounge/WutheringWaves/board/1"
    
    print(f"\n3. 명조 튜닝 보드 테스트: {ww_tuning_url}")
    try:
        posts = fetch_board_posts(ww_tuning_url, max_items=5)
        print(f"   발견된 게시글 수: {len(posts)}")
        
        for i, post in enumerate(posts[:3]):
            print(f"   {i+1}. {post['title'][:60]}...")
            print(f"      URL: {post['url']}")
            print(f"      본문 길이: {len(post.get('body', ''))}")
            
    except Exception as e:
        print(f"   명조 튜닝 보드 테스트 실패: {e}")
    
    # 명조 방송 보드 테스트
    print(f"\n4. 명조 방송 보드 테스트: {ww_broadcast_url}")
    try:
        posts = fetch_board_posts(ww_broadcast_url, max_items=5)
        print(f"   발견된 게시글 수: {len(posts)}")
        
        for i, post in enumerate(posts[:3]):
            print(f"   {i+1}. {post['title'][:60]}...")
            print(f"      URL: {post['url']}")
            print(f"      본문 길이: {len(post.get('body', ''))}")
            
    except Exception as e:
        print(f"   명조 방송 보드 테스트 실패: {e}")

def test_parsing():
    print("\n=== 파싱 로직 테스트 ===")
    
    nikke_update_url = "https://game.naver.com/lounge/nikke/board/48"
    nikke_broadcast_url = "https://game.naver.com/lounge/nikke/board/11"
    ww_tuning_url = "https://game.naver.com/lounge/WutheringWaves/board/28"
    ww_broadcast_url = "https://game.naver.com/lounge/WutheringWaves/board/1"
    
    try:
        print("1. 니케 파싱 테스트...")
        nikke_updates = parse_nikke(nikke_update_url, nikke_broadcast_url, limit=5)
        print(f"   니케 업데이트 항목: {len(nikke_updates)}개")
        for update in nikke_updates:
            print(f"   - {update['description']} ({update['update_date']})")
        
        print("2. 명조 파싱 테스트...")
        ww_updates = parse_ww(ww_tuning_url, ww_broadcast_url, limit=5)
        print(f"   명조 업데이트 항목: {len(ww_updates)}개")
        for update in ww_updates:
            print(f"   - {update['description']} ({update['update_date']})")
            
    except Exception as e:
        print(f"파싱 테스트 실패: {e}")

def test_full_scraper():
    print("\n=== 전체 스크래퍼 테스트 ===")
    
    # 기존 데이터 백업
    backup_path = "data/updates_backup.json"
    if os.path.exists("data/updates.json"):
        with open("data/updates.json", "r", encoding="utf-8") as f:
            backup_data = json.load(f)
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        print(f"기존 데이터를 {backup_path}에 백업했습니다.")
    
    try:
        # 스크래퍼 실행
        from scrape_lounge import main
        main()
        print("스크래퍼 실행 완료!")
        
        # 결과 확인
        if os.path.exists("data/updates.json"):
            with open("data/updates.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"총 업데이트 항목 수: {len(data)}")
            
            # 최근 항목들 확인
            recent_items = [item for item in data if item.get('game_id') in ['nikke', 'ww']][-5:]
            print("최근 니케/명조 항목들:")
            for item in recent_items:
                print(f"  - {item.get('game_id')}: {item.get('description', '')[:50]}...")
        
    except Exception as e:
        print(f"전체 스크래퍼 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lounge_scraping()
    test_parsing()
    test_full_scraper()
