import os
import logging
import requests
import re
import math
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

LOCKER_SITE_URL = os.environ.get('LOCKER_SITE_URL', 'https://metro.akilocker.biz/index.html?lgId=tokyometro')
LOCKER_EXTRA_SOURCES = os.environ.get('LOCKER_EXTRA_SOURCES', '')  # 逗號分隔 URL 清單

def _parse_vacancy_info(text: str):
    """從文字中嘗試解析空位狀態與可用數量。
    返回 (has_vacancy: Optional[bool], available_slots: Optional[int])。
    """
    if not text:
        return None, None
    try:
        lowered = text.lower()
        available_slots = None
        has_vacancy = None

        # 中文數量
        m = re.search(r'(?:空位|剩餘|剩下)\s*[:：]?\s*(\d+)\s*(?:個|位|格|台)?', text)
        if m:
            available_slots = int(m.group(1))
            has_vacancy = available_slots > 0

        # 日文數量 e.g. 空き3台 / 空き 2
        if available_slots is None:
            m = re.search(r'空き\s*[:：]?\s*(\d+)\s*(?:台|個)?', text)
            if m:
                available_slots = int(m.group(1))
                has_vacancy = available_slots > 0

        # 英文數量 e.g. available 3 / 3 available / free 2
        if available_slots is None:
            m = re.search(r'(?:available|free)\s*(\d+)', lowered)
            if m:
                available_slots = int(m.group(1))
                has_vacancy = available_slots > 0
            else:
                m = re.search(r'(\d+)\s*(?:available|free|slots?)', lowered)
                if m:
                    available_slots = int(m.group(1))
                    has_vacancy = available_slots > 0

        # 狀態詞（無數量時嘗試判斷）
        if has_vacancy is None:
            # 中文/日文/英文常見詞
            if re.search(r'(?:有空|尚有|還有|未滿|可用|可租|可放|空きあり|空有り|空いている|available|vacancy)', lowered):
                has_vacancy = True
            elif re.search(r'(?:滿|客滿|無空位|沒有空位|無位|満|満了|満杯|full|sold\s*out)', lowered):
                has_vacancy = False

        return has_vacancy, available_slots
    except Exception:
        return None, None

def _extract_lat_lng_from_text(text: str):
    if not text:
        return None
    # 常見格式：...q=lat,lng 或 ...query=lat,lng 或文字中直接出現 lat,lng
    m = re.search(r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)', text)
    if not m:
        return None
    try:
        return float(m.group(1)), float(m.group(2))
    except Exception:
        return None

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _scrape_site_for_lockers(url: str, headers: dict):
    resp = requests.get(url, headers=headers, timeout=12)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    # 專用解析：coinlocker-navi（例：https://www.coinlocker-navi.com/tokyo/area/tokyo/）
    if 'coinlocker-navi.com' in url:
        items = []
        for a in soup.find_all('a', href=True):
            text = a.get_text(" ", strip=True)
            href = a['href']
            # 只抽取包含 MAP 文字或 Google Maps 連結的鏈接
            if not (('maps' in href) or (re.search(r'\bMAP\b', text, re.I))):
                continue

            latlng = _extract_lat_lng_from_text(href) or _extract_lat_lng_from_text(text)

            # 向上尋找包含附近說明的容器
            container = a
            for _ in range(4):
                if container and container.parent:
                    container = container.parent
                    if len(container.get_text(" ", strip=True)) > 40:
                        break
            block_text = container.get_text("\n", strip=True) if container else ''

            # 嘗試在該區塊中挑較像名稱的一行
            name = None
            for line in [ln.strip() for ln in block_text.split('\n') if ln.strip()]:
                if ('ロッカー' in line) or ('駅' in line) or (8 <= len(line) <= 40):
                    name = line
                    break
            if not name:
                # 再往上找標題元素
                title_el = None
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b']:
                    title_el = container.find_previous(tag)
                    if title_el:
                        break
                name = title_el.get_text(strip=True) if title_el else '附近置物點'

            has_vacancy, available_slots = _parse_vacancy_info(block_text)

            items.append({
                'name': name,
                'address': '—',
                'map_uri': href,
                'latlng': latlng,
                'has_vacancy': has_vacancy,
                'available_slots': available_slots
            })
        return items
    selectors = ['.locker-item', '.item', '.card', '[class*="locker"]', '[data-type*="locker"]', 'li']
    elements = []
    for sel in selectors:
        elements = soup.select(sel)
        if elements:
            break
    items = []
    for el in elements:
        try:
            title_el = (
                el.find(['h1', 'h2', 'h3', 'h4', 'h5']) or
                el.find(class_=lambda c: c and ('title' in c or 'name' in c))
            )
            name = title_el.get_text(strip=True) if title_el else None
            address_el = el.find(class_=lambda c: c and ('address' in c or 'location' in c))
            address = address_el.get_text(strip=True) if address_el else None
            latlng = None
            map_uri = None
            for a in el.find_all('a', href=True):
                latlng = _extract_lat_lng_from_text(a['href']) or _extract_lat_lng_from_text(a.get_text(" ", strip=True))
                if latlng:
                    map_uri = a['href']
                    break
            if not latlng:
                latlng = _extract_lat_lng_from_text(el.get_text(" ", strip=True))
            # 嘗試從此元素文本解析空位資訊
            block_text = el.get_text("\n", strip=True)
            has_vacancy, available_slots = _parse_vacancy_info(block_text)
            if name or address or latlng:
                items.append({
                    'name': name or '附近置物點',
                    'address': address or '—',
                    'map_uri': map_uri or url,
                    'latlng': latlng,
                    'has_vacancy': has_vacancy,
                    'available_slots': available_slots
                })
        except Exception:
            continue
    return items

def fetch_nearby_lockers(lat: float, lng: float, max_items: int = 3):
    """從多個置物櫃來源網站爬取清單，解析座標，依距離排序回傳最近 max_items 筆。"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
        }
        urls = []
        if LOCKER_SITE_URL:
            urls.append(LOCKER_SITE_URL)
        if LOCKER_EXTRA_SOURCES:
            urls.extend([u.strip() for u in LOCKER_EXTRA_SOURCES.split(',') if u.strip()])

        candidates = []
        seen = set()
        for url in urls:
            try:
                items = _scrape_site_for_lockers(url, headers)
                for item in items:
                    key = (item.get('name'), item.get('address'), item.get('map_uri'))
                    if key in seen:
                        continue
                    seen.add(key)
                    if item['latlng']:
                        lat2, lng2 = item['latlng']
                        item['distance_km'] = _haversine_km(lat, lng, lat2, lng2)
                    else:
                        item['distance_km'] = None
                    candidates.append(item)
            except Exception as e:
                logger.warning(f"來源抓取失敗 {url}: {e}")

        # 先過濾出有距離的，按距離排序；若不足，再補無距離者
        with_distance = [c for c in candidates if c['distance_km'] is not None]
        without_distance = [c for c in candidates if c['distance_km'] is None]
        with_distance.sort(key=lambda x: x['distance_km'])
        lockers_sorted = with_distance + without_distance

        final = []
        for c in lockers_sorted[:max_items]:
            final.append({
                'name': c['name'],
                'address': c['address'],
                'rating': None,
                'map_uri': c['map_uri'],
                'distance_km': c['distance_km'],
                'has_vacancy': c.get('has_vacancy'),
                'available_slots': c.get('available_slots')
            })
        return final
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
        uri = item.get('map_uri')
        distance_km = item.get('distance_km')
        distance_text = f"距離：約 {distance_km:.1f} 公里" if isinstance(distance_km, (int, float)) else None
        has_vacancy = item.get('has_vacancy')
        available_slots = item.get('available_slots')
        if has_vacancy is True:
            vacancy_text = f"空位：有{f'（約{available_slots}）' if isinstance(available_slots, int) else ''}"
            vacancy_color = "#0E7A0D"  # 綠色
        elif has_vacancy is False:
            vacancy_text = "空位：已滿"
            vacancy_color = "#B00020"  # 紅色
        else:
            vacancy_text = None
            vacancy_color = "#555555"
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
                    *(([{"type": "text", "text": distance_text, "size": "sm", "color": "#555555", "margin": "sm"}] if distance_text else [])),
                    *(([{"type": "text", "text": vacancy_text, "size": "sm", "color": vacancy_color, "margin": "sm"}] if vacancy_text else []))
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

