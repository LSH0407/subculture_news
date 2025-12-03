#!/usr/bin/env python3
"""
빠른 업데이트 추가 스크립트
X(트위터)나 다른 곳에서 발견한 정보를 빠르게 추가
"""
import sys
import io
import json
from datetime import datetime

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def add_update():
    """대화형으로 업데이트 추가"""
    print("=" * 60)
    print("빠른 업데이트 추가")
    print("=" * 60)
    
    # 게임 선택
    games = {
        "1": "star_rail",
        "2": "zzz",
        "3": "nikke",
        "4": "ww",
    }
    
    print("\n게임 선택:")
    print("1. 붕괴: 스타레일")
    print("2. 젠레스 존 제로")
    print("3. 승리의 여신: 니케")
    print("4. 명조")
    
    game_choice = input("\n번호 입력: ").strip()
    game_id = games.get(game_choice)
    
    if not game_id:
        print("❌ 잘못된 선택")
        return
    
    # 정보 입력
    print(f"\n{game_id} 업데이트 정보 입력:")
    
    description = input("설명 (예: [이벤트] 워프 「키레네」): ").strip()
    url = input("URL: ").strip()
    
    start_date = input("시작 날짜 (YYYY-MM-DD 또는 MM/DD): ").strip()
    # MM/DD 형식이면 현재 연도 추가
    if "/" in start_date and len(start_date.split("/")) == 2:
        month, day = start_date.split("/")
        start_date = f"{datetime.now().year}-{int(month):02d}-{int(day):02d}"
    
    end_date = input("종료 날짜 (YYYY-MM-DD 또는 MM/DD, 없으면 Enter): ").strip()
    if end_date and "/" in end_date and len(end_date.split("/")) == 2:
        month, day = end_date.split("/")
        end_date = f"{datetime.now().year}-{int(month):02d}-{int(day):02d}"
    
    version = input("버전 (선택사항, 없으면 Enter): ").strip()
    
    # 업데이트 객체 생성
    update = {
        "game_id": game_id,
        "version": version,
        "update_date": start_date,
        "description": description,
        "url": url,
    }
    
    if end_date:
        update["end_date"] = end_date
    
    # 확인
    print("\n" + "=" * 60)
    print("추가할 업데이트:")
    print("=" * 60)
    for k, v in update.items():
        print(f"  {k}: {v}")
    
    confirm = input("\n추가하시겠습니까? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ 취소됨")
        return
    
    # 기존 데이터 로드
    try:
        with open('data/updates.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    
    # 중복 체크
    def key(u):
        return f"{u.get('game_id')}|{u.get('update_date')}|{u.get('description','')[:40]}"
    
    if key(update) in {key(u) for u in data}:
        print("\n⚠️  이미 존재하는 업데이트입니다!")
        return
    
    # 추가
    data.append(update)
    
    with open('data/updates.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 업데이트 추가 완료!")
    print(f"총 업데이트 수: {len(data)}")

if __name__ == "__main__":
    add_update()

