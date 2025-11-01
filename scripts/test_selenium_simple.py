#!/usr/bin/env python3
"""
간단한 Selenium 테스트
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def test_selenium_simple():
    """간단한 Selenium 테스트"""
    print("=== Selenium 간단 테스트 ===")
    
    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # 니케 게시판 접근
        nikke_url = "https://game.naver.com/lounge/nikke/board/48"
        print(f"니케 게시판 접근: {nikke_url}")
        
        driver.get(nikke_url)
        
        # 페이지 로딩 대기 (더 긴 시간)
        print("페이지 로딩 대기 중...")
        time.sleep(10)  # 10초 대기
        
        # 게시글이 로드될 때까지 대기
        try:
            print("게시글 로딩 대기 중...")
            wait = WebDriverWait(driver, 20)
            
            # 다양한 선택자로 시도
            selectors_to_wait = [
                "a[class*='title']",
                "[class*='post']",
                "[class*='board']",
                ".list",
                "[data-testid]"
            ]
            
            element_found = None
            for selector in selectors_to_wait:
                try:
                    print(f"선택자 '{selector}' 대기 중...")
                    element_found = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"선택자 '{selector}'로 요소 발견!")
                    break
                except:
                    continue
            
            if not element_found:
                print("특정 선택자로 요소를 찾지 못함, 일반적인 대기 후 진행")
                time.sleep(5)
            
        except Exception as e:
            print(f"요소 대기 실패: {e}")
        
        # 페이지 소스 가져오기
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        print(f"로딩된 페이지 크기: {len(html)} 문자")
        
        # 다양한 선택자로 게시글 찾기
        selectors_to_try = [
            "a[class*='title']",
            "[class*='post']",
            "[class*='board']", 
            "a[href*='detail']",
            "[data-testid*='post']",
            "[data-testid*='title']",
            ".list a",
            "li a"
        ]
        
        for selector in selectors_to_try:
            elements = soup.select(selector)
            print(f"\n선택자 '{selector}': {len(elements)}개 요소 발견")
            if elements:
                for i, elem in enumerate(elements[:3]):
                    text = elem.get_text(strip=True)
                    href = elem.get("href")
                    print(f"  {i+1}. {text[:50]}...")
                    if href:
                        print(f"      href: {href}")
                    
                    # 특수모집 관련 키워드 체크
                    if any(keyword in text for keyword in ['특수모집', '합류', '모집', '업데이트']):
                        print(f"      *** 관련 키워드 발견! ***")
        
        # HTML 일부 출력 (디버깅용)
        print(f"\n=== HTML 샘플 (처음 1000자) ===")
        print(html[:1000])
        
    except Exception as e:
        print(f"Selenium 테스트 실패: {e}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_selenium_simple()


