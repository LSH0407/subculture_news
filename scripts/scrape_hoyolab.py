import json
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup


BASE = "https://www.hoyolab.com"


def fetch_posts(author_id: str, limit: int = 20) -> List[Dict]:
    """Fetch latest posts from HoYoLAB author page (simple HTML parse)."""
    url = f"{BASE}/accountCenter/postList?id={author_id}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; subculture-news/1.0)"}
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    posts: List[Dict] = []

    # HoYoLAB는 종종 동적이지만, SSR된 링크/타이틀이 포함되는 경우가 있어 대비
    for a in soup.select("a[href*='/article/']"):
        title = a.get_text(strip=True)
        href = a.get("href")
        if not title or not href:
            continue
        if not href.startswith("http"):
            href = BASE + href
        posts.append({"title": title, "url": href})
        if len(posts) >= limit:
            break

    # 본문은 각 글을 개별 요청해서 가져온다 (필요 시)
    for p in posts:
        try:
            pr = requests.get(p["url"], headers=headers, timeout=30)
            pr.raise_for_status()
            psoup = BeautifulSoup(pr.text, "html.parser")
            body = psoup.get_text("\n", strip=True)
            p["body"] = body
        except Exception:
            p["body"] = ""
    return posts


def find_korean_datetime(text: str) -> Tuple[str, str]:
    """Return (iso_datetime_kst, human_md) from strings like '8월 22일 20:30(KST)'.
    If time missing, returns date only ISO (YYYY-MM-DD)."""
    # ex: 8월 22일 20:30(KST)
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*(\d{1,2}):(\d{2})\s*\(KST\)", text)
    if m:
        mm, dd, hh, mi = map(int, m.groups())
        year = datetime.now().year
        dt = datetime(year, mm, dd, hh, mi)
        return dt.strftime("%Y-%m-%dT%H:%M:00+09:00"), f"{mm}/{dd} {hh:02d}:{mi:02d}"
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if m:
        mm, dd = map(int, m.groups())
        year = datetime.now().year
        dt = datetime(year, mm, dd)
        return dt.strftime("%Y-%m-%d"), f"{mm}/{dd}"
    return "", ""


def find_korean_daterange(text: str) -> Tuple[str, str]:
    """Parse a range like '9월 24일 ~ 10월 15일' -> (YYYY-MM-DD, YYYY-MM-DD)."""
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*[~~\-]\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if not m:
        return "", ""
    y = datetime.now().year
    mm1, dd1, mm2, dd2 = map(int, m.groups())
    return datetime(y, mm1, dd1).strftime("%Y-%m-%d"), datetime(y, mm2, dd2).strftime("%Y-%m-%d")


def extract_version(text: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)?)\s*버전", text)
    return m.group(1) if m else ""


def build_desc(start_md: str, end_md: str, lines: List[str]) -> str:
    out = [f"시작일 : {start_md}", f"종료일 : {end_md}"] if start_md and end_md else []
    out.extend(lines)
    return "\n".join(out)


def parse_zzz(posts: List[Dict]) -> List[Dict]:
    results: List[Dict] = []
    # 캐시: 버전→업데이트 안내에서 추출한 업데이트일
    version_to_update_date: Dict[str, str] = {}
    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        ver = extract_version(title + " " + body)
        # 업데이트 안내 → 시작일 캐싱
        if "업데이트 안내" in title and ver:
            dt_iso, md = find_korean_datetime(body)
            if not dt_iso:
                dt_iso, md = find_korean_datetime(title)
            if dt_iso:
                version_to_update_date[ver] = dt_iso.split("T")[0]

    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        url = p["url"]
        ver = extract_version(title + " " + body)
        # 특별 방송 예고
        if "특별 방송 예고" in title:
            dt_iso, md = find_korean_datetime(body)
            if dt_iso and ver:
                results.append({
                    "game_id": "zzz",
                    "version": ver,
                    "update_date": dt_iso,
                    "description": f"{ver} 버전 특별 방송",
                    "url": url,
                })
            continue
        # 기간 한정 채널(상/하)
        if "기간 한정 채널" in title and ver:
            if "상)" in title or "(상" in title:
                start = version_to_update_date.get(ver, "")
                _, end = find_korean_daterange(body)
                if start and end:
                    results.append({
                        "game_id": "zzz",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": build_desc(start.replace("2025-", "").replace("2024-", ""), end.replace("2025-", "").replace("2024-", ""), ["[이벤트] 기간 한정 채널(상)"]),
                        "url": url,
                    })
            elif "하)" in title or "(하" in title:
                start, end = find_korean_daterange(body)
                if start and end:
                    results.append({
                        "game_id": "zzz",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": build_desc(start.replace("2025-", "").replace("2024-", ""), end.replace("2025-", "").replace("2024-", ""), ["[이벤트] 기간 한정 채널(하)"]),
                        "url": url,
                    })
    return results


def parse_star_rail(posts: List[Dict]) -> List[Dict]:
    results: List[Dict] = []
    version_to_update_date: Dict[str, str] = {}
    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        ver = extract_version(title + " " + body)
        if "업데이트 점검 예고" in title and ver:
            dt_iso, _ = find_korean_datetime(body)
            if dt_iso:
                version_to_update_date[ver] = dt_iso.split("T")[0]

    for p in posts:
        title = p["title"]
        body = p.get("body", "")
        url = p["url"]
        ver = extract_version(title + " " + body)
        # 프리뷰 스페셜 프로그램 (제목 끝에 추가정보 없다고 가정)
        if "프리뷰 스페셜 프로그램" in title and ver and "-" not in title and "|" not in title:
            dt_iso, _ = find_korean_datetime(body)
            if dt_iso:
                results.append({
                    "game_id": "star_rail",
                    "version": ver,
                    "update_date": dt_iso,
                    "description": f"{ver} 프리뷰 스페셜 프로그램",
                    "url": url,
                })
            continue
        # 이벤트 워프 (1/2)
        m = re.search(r"이벤트\s*워프\s*\((\d)\)", title)
        if m and ver:
            y = m.group(1)
            if y == "1":
                start = version_to_update_date.get(ver, "")
                _, end = find_korean_daterange(body)
                if start and end:
                    md_s = start.split("-")
                    md_e = end.split("-")
                    desc = build_desc(f"{int(md_s[1])}/{int(md_s[2])}", f"{int(md_e[1])}/{int(md_e[2])}", ["[이벤트] 워프(1)"])
                    results.append({
                        "game_id": "star_rail",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": desc,
                        "url": url,
                    })
            else:
                start, end = find_korean_daterange(body)
                if start and end:
                    md_s = start.split("-")
                    md_e = end.split("-")
                    desc = build_desc(f"{int(md_s[1])}/{int(md_s[2])}", f"{int(md_e[1])}/{int(md_e[2])}", ["[이벤트] 워프(2)"])
                    results.append({
                        "game_id": "star_rail",
                        "version": ver,
                        "update_date": start,
                        "end_date": end,
                        "description": desc,
                        "url": url,
                    })
    return results


def merge_updates(new_updates: List[Dict]) -> None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "updates.json"))
    try:
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []

    # 디듀프 키: game_id + version + update_date + description
    def key(u: Dict) -> str:
        return f"{u.get('game_id')}|{u.get('version','')}|{u.get('update_date')}|{u.get('description','')[:40]}"

    seen = {key(u) for u in existing}
    merged = existing[:]
    added = 0
    for u in new_updates:
        if key(u) in seen:
            continue
        merged.append(u)
        added += 1

    if added:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"HoYoLAB merged: +{added} items")


def main():
    zzz_id = os.getenv("HOYOLAB_ZZZ_AUTHOR", "219270333")
    sr_id = os.getenv("HOYOLAB_SR_AUTHOR", "172534910")
    limit = int(os.getenv("HOYOLAB_LIMIT", "20"))

    all_updates: List[Dict] = []

    try:
        zzz_posts = fetch_posts(zzz_id, limit=limit)
        all_updates += parse_zzz(zzz_posts)
    except Exception as e:
        print("ZZZ scrape failed:", e)

    try:
        sr_posts = fetch_posts(sr_id, limit=limit)
        all_updates += parse_star_rail(sr_posts)
    except Exception as e:
        print("Star Rail scrape failed:", e)

    merge_updates(all_updates)


if __name__ == "__main__":
    main()


