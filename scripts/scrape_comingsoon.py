import json
import os
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser


URL = "https://store.steampowered.com/search/?filter=popularcomingsoon&os=win&l=koreana&cc=kr&page={page}"
APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"


def parse_list(max_pages: int = 3) -> List[Dict]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
    results: List[Dict] = []
    for page in range(1, max_pages + 1):
        html = requests.get(URL.format(page=page), headers=headers, timeout=60)
        html.raise_for_status()
        soup = BeautifulSoup(html.text, "html.parser")
        for row in soup.select("a.search_result_row"):
            name_el = row.select_one("span.title")
            name = name_el.get_text(strip=True) if name_el else ""
            href = row.get("href") or ""
            appid = row.get("data-ds-appid") or ""
            date_el = row.select_one("div.search_released")
            date_txt = date_el.get_text(strip=True) if date_el else ""
            price_el = row.select_one("div.search_price")
            price_txt = price_el.get_text(" ", strip=True) if price_el else ""
            tag_el = row.select_one("div.search_tags")
            genre = tag_el.get_text(" ", strip=True) if tag_el else ""
            
            # 헤더 이미지 URL 추출 (header.jpg 우선, 그 다음 capsule 이미지)
            header_image = ""
            selectors = [
                "img[src*='header.jpg']",
                "img.game_header_image_full",
                "img[class*='header']",
                "img[src*='capsule_616x353']",
                "img[src*='capsule']"
            ]
            
            for selector in selectors:
                header_img_el = row.select_one(selector)
                if header_img_el:
                    header_image = header_img_el.get("src", "")
                    if header_image:
                        # 상대 경로인 경우 절대 경로로 변환
                        if header_image.startswith("//"):
                            header_image = "https:" + header_image
                        elif header_image.startswith("/"):
                            header_image = "https://store.steampowered.com" + header_image
                        break
            
            # 특별 처리: EA SPORTS FC™ 26의 경우 정확한 헤더 이미지 URL 사용
            if "EA SPORTS FC" in name and appid == "3405690":
                header_image = "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/3405690/2d96aa1b06e453cd62dae9029d412f19e61932c3/header.jpg?t=1757323434"
                print(f"Using specific header image for {name}: {header_image}")
            
            # 디버깅: EA SPORTS FC™ 26의 경우 로그 출력
            if "EA SPORTS FC" in name:
                if header_image:
                    print(f"Final header image for {name}: {header_image}")
                else:
                    print(f"No header image found for {name}")
                    # 모든 이미지 요소 확인
                    all_imgs = row.select("img")
                    print(f"All img elements: {[img.get('src', '') for img in all_imgs]}")

            # normalize - 날짜 파싱 개선
            import re
            date_str = "TBA"
            
            # 먼저 연도만 있는지 확인 (예: "2025년", "2025")
            year_only_match = re.match(r'^(\d{4})년?$', date_txt.strip())
            if year_only_match:
                # 연도만 있는 경우 - 원본 형식 유지 (프론트엔드에서 처리)
                date_str = date_txt.strip()
            else:
                try:
                    release_dt = date_parser.parse(date_txt, fuzzy=True)
                    date_str = release_dt.strftime("%Y-%m-%d")
                except Exception:
                    # 파싱 실패시 원본 텍스트 유지
                    date_str = date_txt.strip() if date_txt else "TBA"

            price_norm = price_txt if price_txt else "미표기"

            # 플랫폼 감지 (간단 규칙: 태그/장르 텍스트에 'Nintendo'나 'Switch'가 있으면 스위치)
            platform = 'steam'
            if 'Switch' in genre or 'Nintendo' in genre:
                platform = 'switch'

            results.append({
                "name": name,
                "release_date": date_str,
                "price": price_norm,
                "genres": genre,
                "appid": appid,
                "url": href,
                "platform": platform,
                "header_image": header_image,
            })
    # de-duplicate by appid or (name, release_date)
    seen: set[str] = set()
    uniq: List[Dict] = []
    for r in results:
        key = r.get("appid") or f"{r.get('name')}|{r.get('release_date')}"
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    return uniq


def fetch_appdetails(appid: str) -> Dict:
    params = {
        "appids": appid,
        "cc": "KR",
        "l": "koreana",
    }
    headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
    res = requests.get(APPDETAILS_URL, params=params, headers=headers, timeout=60)
    res.raise_for_status()
    data = res.json()
    app_data = data.get(appid, {}).get("data", {})
    
    # 찜 횟수(wishlist count) 정보 가져오기 - Steam Store 페이지에서 추출
    try:
        store_url = f"https://store.steampowered.com/app/{appid}/?l=koreana&cc=kr"
        store_res = requests.get(store_url, headers=headers, timeout=60)
        if store_res.status_code == 200:
            soup = BeautifulSoup(store_res.text, "html.parser")
            # 찜 횟수는 보통 "X명이 이 게임을 찜 목록에 추가했습니다" 형태로 표시
            wishlist_text_selectors = [
                ".wishlist_status",
                ".game_details .details_block",
                "div:contains('찜')",
            ]
            for selector in wishlist_text_selectors:
                wishlist_el = soup.select_one(selector)
                if wishlist_el:
                    text = wishlist_el.get_text()
                    # "12,345명이 이 게임을 찜" 형태에서 숫자 추출
                    import re
                    match = re.search(r"([\d,]+)\s*명.*?찜", text)
                    if match:
                        wishlist_str = match.group(1).replace(",", "")
                        app_data["wishlist_count"] = int(wishlist_str)
                        break
    except Exception as e:
        # 찜 횟수를 가져오지 못해도 계속 진행
        pass
    
    return app_data

def fetch_store_info(appid: str) -> dict:
    """Steam Store 페이지에서 태그와 발매일을 직접 스크래핑 (한국 기준)"""
    try:
        url = f"https://store.steampowered.com/app/{appid}/?l=koreana&cc=kr"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
        res = requests.get(url, headers=headers, timeout=60)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        tags = []
        release_date = None
        
        # 태그 요소들 찾기 (여러 선택자 시도)
        tag_selectors = [
            "a.app_tag",
            ".app_tag",
            "[data-tooltip-text]",
            ".popular_tags a",
            ".game_tag"
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag_el in tag_elements:
                tag_text = tag_el.get_text(strip=True)
                if tag_text and tag_text not in tags and len(tag_text) < 50:  # 너무 긴 텍스트 제외
                    tags.append(tag_text)
        
        # 한국어로 표시된 발매일 찾기
        release_date_selectors = [
            ".release_date .date",
            ".game_release_date",
            "div.date"
        ]
        
        for selector in release_date_selectors:
            date_el = soup.select_one(selector)
            if date_el:
                date_text = date_el.get_text(strip=True)
                if date_text and date_text != "출시 예정":
                    release_date = date_text
                    break
        
        # 디버깅: 특정 게임의 경우 로그 출력
        if appid == "2947440" or "3229870" in appid:  # SILENT HILL f, Little Nightmares III
            print(f"App {appid}: Store release date = {release_date}, tags = {tags[:3]}")
        
        return {"tags": tags, "release_date": release_date}
    except Exception as e:
        print(f"Failed to fetch store info for {appid}: {e}")
        return {"tags": [], "release_date": None}


def to_updates(entries: List[Dict], months: List[int]) -> List[Dict]:
    # 환경 변수에서 최소 찜 횟수 설정 (기본값: 5000)
    min_wishlist = int(os.getenv("MIN_WISHLIST_COUNT", "5000"))
    
    updates = []
    filtered_count = 0
    
    for e in entries:
        # month filter (keep items with parseable YYYY-MM-DD only)
        try:
            dt = date_parser.parse(e["release_date"]) if e["release_date"] != "TBA" else None
        except Exception:
            dt = None
        if dt and months and dt.month not in months:
            continue
        details = {}
        if e.get("appid"):
            try:
                details = fetch_appdetails(e["appid"])
            except Exception:
                details = {}
        
        # 찜 횟수 필터링
        wishlist_count = details.get("wishlist_count", 0)
        if wishlist_count < min_wishlist:
            filtered_count += 1
            print(f"Filtered out {e['name']} (wishlist: {wishlist_count} < {min_wishlist})")
            continue
        
        # Store 페이지에서 태그와 발매일 수집 (한국 기준)
        store_info = {"tags": [], "release_date": None}
        if e.get("appid"):
            store_info = fetch_store_info(e["appid"])
        
        all_tags = []
        
        # 특별 처리: SILENT HILL f의 경우 수동으로 태그 설정
        if e.get("appid") == "2947440":
            all_tags = ["심리적 공포", "공포", "생존 공포", "풍부한 스토리", "액션"]
        else:
            # Store 페이지 태그 우선 사용
            if store_info["tags"]:
                all_tags.extend(store_info["tags"])
            else:
                # Store 태그가 없으면 API 태그 사용
                if details.get("genres"):
                    all_tags.extend([g.get("description") for g in details["genres"] if g.get("description")])
                
                if details.get("categories"):
                    all_tags.extend([c.get("description") for c in details["categories"] if c.get("description")])
        
        # 중복 제거하고 정렬
        unique_tags = list(dict.fromkeys(all_tags))  # 순서 유지하면서 중복 제거
        tags = ", ".join(unique_tags)
        
        summary = details.get("short_description", "")
        # 고해상도 헤더: appdetails의 header_image 우선 사용
        hi_res_header = details.get("header_image") if isinstance(details, dict) else None
        
        # 발매일 우선순위: Store 페이지 (한국어) > Steam API > 원본
        final_release_date = e["release_date"]
        
        # 1. Store 페이지에서 한국어로 표시된 발매일 사용 (최우선)
        if store_info.get("release_date"):
            try:
                store_date_text = store_info["release_date"]
                # 한국어 날짜 파싱: "2025년 10월 10일" 형식
                store_dt = date_parser.parse(store_date_text, fuzzy=True)
                final_release_date = store_dt.strftime("%Y-%m-%d")
                
                # 디버깅
                if "Little Nightmares" in e["name"] or "풀메탈" in e["name"] or "FullMetal" in e["name"]:
                    print(f"{e['name']}: Store KR date = {store_date_text} -> {final_release_date}")
            except Exception as ex:
                print(f"Failed to parse Store date for {e['name']}: {store_info.get('release_date')} - {ex}")
        
        # 2. Store 페이지에서 가져오지 못한 경우 Steam API 사용
        elif details and details.get("release_date"):
            api_date_str = details["release_date"].get("date", "")
            if api_date_str:
                try:
                    # Steam API 날짜 형식: "9 Oct, 2025" 또는 "Oct 9, 2025"
                    api_dt = date_parser.parse(api_date_str, fuzzy=True)
                    final_release_date = api_dt.strftime("%Y-%m-%d")
                    
                    # 디버깅
                    if "Little Nightmares" in e["name"] or "풀메탈" in e["name"] or "FullMetal" in e["name"]:
                        print(f"{e['name']}: API date = {api_date_str} -> {final_release_date}")
                except Exception as ex:
                    print(f"Failed to parse API date for {e['name']}: {api_date_str} - {ex}")
        
        updates.append({
            "game_id": f"steam_{e['appid']}" if e.get("appid") else f"coming_{e['name']}",
            "version": "",
            "update_date": final_release_date,
            "description": f"발매예정 · {e['genres']}",
            "name": e["name"],
            "url": e.get("url", ""),
            "platform": e.get("platform", "steam"),
            "tags": tags,
            "summary": summary,
            "header_image": hi_res_header or e.get("header_image", ""),
            "wishlist_count": wishlist_count,  # 찜 횟수 추가
        })
    
    print(f"\n필터링 요약:")
    print(f"  총 수집: {len(entries)}개")
    print(f"  필터링됨: {filtered_count}개 (찜 횟수 < {min_wishlist})")
    print(f"  최종 추가: {len(updates)}개")
    
    return updates


def main():
    # 당일 기준 롤링 개월 수 계산 (기본 3개월)
    rolling = int(os.getenv("ROLLING_MONTHS", "3"))
    now = datetime.now(timezone.utc)
    months = [(now + relativedelta(months=i)).month for i in range(max(1, rolling))]
    entries = parse_list(max_pages=int(os.getenv("MAX_PAGES", "10")))
    updates = to_updates(entries, months)
    updates.sort(key=lambda x: x["update_date"])

    updates_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "updates.json"))
    try:
        with open(updates_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []

    # Remove previous steam_/coming_ entries in target months to avoid duplicates
    def is_target(entry: Dict) -> bool:
        gid = str(entry.get("game_id", ""))
        if not (gid.startswith("steam_") or gid.startswith("coming_")):
            return False
        try:
            d = date_parser.parse(entry.get("update_date", ""))
            return d.month in months
        except Exception:
            return False

    # 기존 Steam 게임들을 제거
    filtered = [e for e in existing if not is_target(e)]
    
    # 추가 중복 제거: 같은 이름과 날짜를 가진 게임들 제거
    def is_duplicate(entry: Dict, new_entries: List[Dict]) -> bool:
        for new_entry in new_entries:
            if (entry.get("name") == new_entry.get("name") and 
                entry.get("update_date") == new_entry.get("update_date") and
                entry.get("platform") == new_entry.get("platform")):
                return True
        return False
    
    # 새로운 업데이트에서 중복 제거
    unique_updates = []
    for update in updates:
        if not is_duplicate(update, unique_updates):
            unique_updates.append(update)
    
    merged = filtered + unique_updates

    with open(updates_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(updates)} upcoming coming-soon entries for months={months} (rolling={rolling})")


if __name__ == "__main__":
    main()

