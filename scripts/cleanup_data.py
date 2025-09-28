#!/usr/bin/env python3
"""
데이터 정리 스크립트: 중복 제거 및 가격 정보 정리
"""

import json
import os
from typing import Dict, List


def clean_description(description: str) -> str:
    """description에서 가격 정보 제거"""
    if not description:
        return description
    
    # "발매예정 · 장르 · 미표기" -> "발매예정 · 장르"
    if " · 미표기" in description:
        description = description.replace(" · 미표기", "")
    
    # "발매예정 · · 미표기" -> "발매예정"
    if " · · 미표기" in description:
        description = description.replace(" · · 미표기", "")
    
    # "발매예정 · ·" -> "발매예정"
    if " · ·" in description:
        description = description.replace(" · ·", "")
    
    return description


def remove_duplicates(updates: List[Dict]) -> List[Dict]:
    """중복 제거: 같은 이름, 날짜, 플랫폼을 가진 항목들 제거"""
    seen = set()
    unique_updates = []
    
    for update in updates:
        # 중복 체크 키: 이름 + 날짜 + 플랫폼
        key = (
            update.get("name", ""),
            update.get("update_date", ""),
            update.get("platform", "")
        )
        
        if key not in seen:
            seen.add(key)
            unique_updates.append(update)
        else:
            print(f"중복 제거: {update.get('name', 'Unknown')} ({update.get('update_date', 'Unknown')})")
    
    return unique_updates


def main():
    """메인 함수"""
    updates_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "updates.json"))
    
    # 기존 데이터 로드
    try:
        with open(updates_path, "r", encoding="utf-8") as f:
            updates = json.load(f)
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        return
    
    print(f"원본 데이터: {len(updates)}개 항목")
    
    # 1. description 정리 (가격 정보 제거)
    cleaned_count = 0
    for update in updates:
        original_desc = update.get("description", "")
        cleaned_desc = clean_description(original_desc)
        if original_desc != cleaned_desc:
            update["description"] = cleaned_desc
            cleaned_count += 1
    
    print(f"가격 정보 제거: {cleaned_count}개 항목")
    
    # 2. 중복 제거
    original_count = len(updates)
    updates = remove_duplicates(updates)
    removed_count = original_count - len(updates)
    
    print(f"중복 제거: {removed_count}개 항목")
    print(f"정리 후 데이터: {len(updates)}개 항목")
    
    # 정리된 데이터 저장
    try:
        with open(updates_path, "w", encoding="utf-8") as f:
            json.dump(updates, f, ensure_ascii=False, indent=2)
        print("데이터 정리 완료!")
    except Exception as e:
        print(f"데이터 저장 실패: {e}")


if __name__ == "__main__":
    main()
