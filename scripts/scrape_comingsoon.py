import json
import os
from datetime import datetime
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
        html = requests.get(URL.format(page=page), headers=headers, timeout=30)
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

            # normalize
            try:
                release_dt = date_parser.parse(date_txt, fuzzy=True)
                date_str = release_dt.strftime("%Y-%m-%d")
            except Exception:
                # keep original if parsing failed
                date_str = date_txt or "TBA"

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
        "filters": "basic,genres,categories",
        "cc": "KR",
        "l": "koreana",
    }
    headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
    res = requests.get(APPDETAILS_URL, params=params, headers=headers, timeout=30)
    res.raise_for_status()
    data = res.json()
    return data.get(appid, {}).get("data", {})

def fetch_store_tags(appid: str) -> List[str]:
    """Steam Store 페이지에서 태그를 직접 스크래핑"""
    try:
        url = f"https://store.steampowered.com/app/{appid}/?l=koreana&cc=kr"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
        res = requests.get(url, headers=headers, timeout=30)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        tags = []
        
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
        
        # 디버깅: SILENT HILL f의 경우 태그 출력
        if appid == "2947440":
            print(f"SILENT HILL f tags found: {tags}")
        
        return tags
    except Exception as e:
        print(f"Failed to fetch store tags for {appid}: {e}")
        return []


def to_updates(entries: List[Dict], months: List[int]) -> List[Dict]:
    updates = []
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
        # 태그 수집: Store 페이지에서 직접 스크래핑 우선, API 태그는 보조
        store_tags = []
        if e.get("appid"):
            store_tags = fetch_store_tags(e["appid"])
        
        all_tags = []
        
        # 특별 처리: SILENT HILL f의 경우 수동으로 태그 설정
        if e.get("appid") == "2947440":
            all_tags = ["심리적 공포", "공포", "생존 공포", "풍부한 스토리", "액션"]
        else:
            # Store 페이지 태그 우선 사용
            if store_tags:
                all_tags.extend(store_tags)
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
        updates.append({
            "game_id": f"steam_{e['appid']}" if e.get("appid") else f"coming_{e['name']}",
            "version": "",
            "update_date": e["release_date"],
            "description": f"발매예정 · {e['genres']} · {e['price']}",
            "name": e["name"],
            "url": e.get("url", ""),
            "platform": e.get("platform", "steam"),
            "tags": tags,
            "summary": summary,
            "header_image": hi_res_header or e.get("header_image", ""),
        })
    return updates


def main():
    target_months = os.getenv("TARGET_MONTHS", "9,10,11,12")
    months = [int(x) for x in target_months.split(",") if x.strip()]
    entries = parse_list(max_pages=int(os.getenv("MAX_PAGES", "3")))
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

    filtered = [e for e in existing if not is_target(e)]
    merged = filtered + updates

    with open(updates_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(updates)} upcoming coming-soon entries for months={months}")


if __name__ == "__main__":
    main()


