import os
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

LOCKER_SITE_URL = os.environ.get('LOCKER_SITE_URL', 'https://tripfrontend.vercel.app/linelocker')

def fetch_nearby_lockers(lat: float, lng: float, max_items: int = 3):
    """從自家置物櫃網站頁面爬取附近置物資訊（不依賴 Google API）。"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
        }
        # 嘗試以查詢參數帶入座標，若站點支援則可回傳附近結果
        url = f"{LOCKER_SITE_URL}?lat={lat}&lng={lng}"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, 'html.parser')

        # 寬鬆選擇器，盡可能找出清單項目
        selectors = [
            '.locker-item',
            '.item',
            '[class*="locker"]',
            '[data-type*="locker"]',
            'li',
            '.card'
        ]

        elements = []
        for sel in selectors:
            elements = soup.select(sel)
            if elements:
                break

        lockers = []
        for el in elements:
            try:
                # 名稱：優先使用標題標籤或含 name/title 的 class
                title_el = (
                    el.find(['h1', 'h2', 'h3', 'h4', 'h5']) or
                    el.find(class_=lambda c: c and ('title' in c or 'name' in c))
                )
                name = title_el.get_text(strip=True) if title_el else None

                # 地址：找含 address/location 的 class 或文字
                address_el = el.find(class_=lambda c: c and ('address' in c or 'location' in c))
                address = address_el.get_text(strip=True) if address_el else None

                # 導航連結：找包含 map 的連結
                link_el = el.find('a', href=True)
                map_uri = None
                if link_el and ('map' in link_el['href'] or 'maps' in link_el['href']):
                    map_uri = link_el['href']
                if not map_uri:
                    # 回退到站內頁面
                    map_uri = LOCKER_SITE_URL

                if name or address:
                    lockers.append({
                        'name': name or '附近置物點',
                        'address': address or '—',
                        'rating': None,
                        'map_uri': map_uri
                    })

                if len(lockers) >= max_items:
                    break
            except Exception:
                continue

        return lockers
    except Exception as e:
        logger.error(f"爬取置物櫃網站失敗: {e}")
        return []

def build_lockers_carousel(lockers):
    if not lockers:
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "找不到附近的置物櫃資料", "align": "center", "color": "#666666"}
                ],
                "paddingAll": "20px"
            }
        }
    bubbles = []
    for idx, item in enumerate(lockers, 1):
        name = item.get('name')
        addr = item.get('address')
        rating = item.get('rating')
        uri = item.get('map_uri')
        rating_text = f"評分：{rating}" if rating else "—"
        bubbles.append({
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [{"type": "text", "text": f"🛅 附近置物櫃 #{idx}", "weight": "bold", "size": "lg", "color": "#ffffff", "align": "center"}],
                "backgroundColor": "#FFA500",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": name, "weight": "bold", "size": "md", "color": "#333333", "wrap": True},
                    {"type": "text", "text": addr, "size": "sm", "color": "#555555", "wrap": True, "margin": "sm"},
                    {"type": "text", "text": rating_text, "size": "sm", "color": "#555555", "margin": "sm"}
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "action": {"type": "uri", "label": "導航", "uri": uri}, "style": "primary", "color": "#FFA500", "height": "sm"}
                ],
                "paddingAll": "20px"
            }
        })
    return {"type": "carousel", "contents": bubbles}

