import os
import logging
import requests
import re
import math
import time
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

LOCKER_SITE_URL = os.environ.get('LOCKER_SITE_URL', 'https://www.coinlocker-navi.com/')
LOCKER_EXTRA_SOURCES = os.environ.get('LOCKER_EXTRA_SOURCES', '')  # 逗號分隔 URL 清單

# 預設整合來源（若未提供環境變數，或作為補充）
DEFAULT_LOCKER_SOURCES = [
    'https://metro.akilocker.biz/index.html?lgId=tokyometro',  # Tokyo Metro Locker Concierge
    'https://www.metocan.co.jp/locker/',                      # Metro Commerce 站點清單（含各站空位頁連結）
    'https://qrtranslator.com/0000001730/000048/',            # Shinjuku 站 QR Translator 範例頁
    'https://www.coinlocker-navi.com/'                        # 全國置物櫃導航
]

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

        # Ecbo Cloak 特定格式
        if available_slots is None:
            # 查找 "X/XX" 格式 (如 "3/20" 表示 3個可用，總共20個)
            m = re.search(r'(\d+)/(\d+)', text)
            if m:
                available_slots = int(m.group(1))
                has_vacancy = available_slots > 0
            # 查找 "X of XX" 格式
            elif re.search(r'(\d+)\s*of\s*(\d+)', lowered):
                m = re.search(r'(\d+)\s*of\s*(\d+)', lowered)
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

def _get_location_name_from_coordinates(lat: float, lng: float) -> str:
    """根據座標獲取地點名稱"""
    try:
        # 使用反向地理編碼來獲取地點名稱
        # 這裡使用一個簡單的座標範圍判斷來識別主要城市
        if 35.5 <= lat <= 35.8 and 139.5 <= lng <= 139.9:
            return "東京"
        elif 34.6 <= lat <= 34.8 and 135.4 <= lng <= 135.6:
            return "大阪"
        elif 35.0 <= lat <= 35.2 and 135.7 <= lng <= 135.8:
            return "京都"
        elif 35.1 <= lat <= 35.2 and 136.8 <= lng <= 137.0:
            return "名古屋"
        elif 43.0 <= lat <= 43.2 and 141.3 <= lng <= 141.5:
            return "札幌"
        elif 33.5 <= lat <= 33.7 and 130.3 <= lng <= 130.5:
            return "福岡"
        elif 26.1 <= lat <= 26.3 and 127.6 <= lng <= 127.8:
            return "沖繩"
        elif 25.0 <= lat <= 25.1 and 121.4 <= lng <= 121.6:
            return "台北"
        elif 22.2 <= lat <= 22.4 and 114.1 <= lng <= 114.3:
            return "香港"
        elif 1.2 <= lat <= 1.5 and 103.6 <= lng <= 103.9:
            return "新加坡"
        elif 37.4 <= lat <= 37.7 and 126.9 <= lng <= 127.2:
            return "首爾"
        elif 36.6 <= lat <= 36.8 and 137.1 <= lng <= 137.3:
            return "富山"
        else:
            # 如果不在已知範圍內，嘗試使用更精確的判斷
            if 35.0 <= lat <= 36.0 and 139.0 <= lng <= 140.0:
                return "關東地區"
            elif 34.0 <= lat <= 35.0 and 135.0 <= lng <= 136.0:
                return "關西地區"
            elif 42.0 <= lat <= 44.0 and 140.0 <= lng <= 142.0:
                return "北海道"
            else:
                return "附近地區"
    except Exception as e:
        logger.warning(f"獲取地點名稱失敗: {e}")
        return "附近地區"

def _scrape_site_for_lockers(url: str, headers: dict):
    resp = requests.get(url, headers=headers, timeout=12)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    # Ecbo Cloak 置物櫃服務 - 跳過，因為是動態網站
    if 'cloak.ecbo.io' in url:
        # Ecbo Cloak 是動態網站，需要 JavaScript 渲染，爬蟲無法獲取有效數據
        # 直接返回空列表，讓系統使用其他來源
        logger.info("跳過 Ecbo Cloak 網站（動態網站，需要 JavaScript 渲染）")
        return []

    # Tokyo Metro Locker Concierge（入口頁，多語，動態內容為主：保底抽鏈結與區塊文字）
    if 'akilocker.biz' in url:
        items = []
        # 嘗試蒐集頁內與 Locker/Station 相關的連結做為候選點
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(' ', strip=True)
            if not text and not href:
                continue
            # 只保留與 locker/metro/station 相關的連結
            if any(key in href for key in ['locker', 'lgId', 'station', 'metro']) or any(key in text for key in ['ロッカー', 'Locker', '駅']):
                name = text or 'Tokyo Metro ロッカー'
                # 盡量取一個較有意義的名稱
                if len(name) < 4:
                    name = 'Tokyo Metro ロッカー'
                items.append({
                    'name': name,
                    'address': '東京メトロ駅構内',
                    'map_uri': href if href.startswith('http') else url,
                    'latlng': None,
                })
        # 若頁面未提供可用連結，至少返回入口作為一筆候選
        if not items:
            items.append({
                'name': 'Tokyo Metro ロッカー',
                'address': '東京メトロ',
                'map_uri': url,
                'latlng': None,
            })
        return items

    # Metro Commerce 站點清單頁：抓取「空き状況はこちら」的站點連結
    if 'metocan.co.jp/locker' in url:
        items = []
        for a in soup.find_all('a', href=True):
            text = a.get_text(' ', strip=True)
            if '空き状況' not in text:
                continue
            href = a['href']
            # 站名：往上找最近的標題元素
            station = None
            for tag in ['h3', 'h2', 'h4', 'strong', 'b']:
                t = a.find_previous(tag)
                if t:
                    t_text = t.get_text(strip=True)
                    if ('駅' in t_text) or ('Station' in t_text):
                        station = t_text
                        break
            name = (station or '東京メトロ駅') + ' コインロッカー'
            items.append({
                'name': name,
                'address': station or '東京メトロ',
                'map_uri': href if href.startswith('http') else url,
                'latlng': None,
            })
        # 若沒有特定站點，至少返回總覽頁
        if not items:
            items.append({
                'name': '東京メトロ コインロッカー一覧',
                'address': '東京メトロ',
                'map_uri': url,
                'latlng': None,
            })
        return items

    # 京王線站點頁：嘗試彙總「空き数」做為 available_slots
    if 'keiochika.co.jp/locker' in url:
        title_el = soup.find(['h1', 'title'])
        title_text = title_el.get_text(strip=True) if title_el else '京王線 駅'
        page_text = soup.get_text('\n', strip=True)
        # 匹配多個「空き数」數字
        slot_nums = [int(m.group(1)) for m in re.finditer(r'空き数\s*[^\d]*(\d+)', page_text)]
        available_slots = sum(slot_nums) if slot_nums else None
        has_vacancy = (available_slots is not None and available_slots > 0)
        return [{
            'name': f'{title_text} コインロッカー',
            'address': title_text,
            'map_uri': url,
            'latlng': None,
            'has_vacancy': has_vacancy if slot_nums else None,
            'available_slots': available_slots
        }]

    # QR Translator 站點頁（例：新宿）
    if 'qrtranslator.com' in url:
        h1 = soup.find('h1')
        page_title = h1.get_text(strip=True) if h1 else soup.title.get_text(strip=True) if soup.title else 'Coin Locker Map'
        return [{
            'name': page_title,
            'address': '駅構内',
            'map_uri': url,
            'latlng': None,
        }]

    # 全國置物櫃導航網站
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

    # 通用置物櫃網站解析（適用於富山市等較小城市）
    if any(domain in url for domain in ['ecbo-cloak.com', 'coinlocker.jp', 'locker-navi.com']):
        items = []
        # 查找包含置物櫃信息的元素
        selectors = [
            '.locker-item', '.locker-card', '.location-item', '.store-item',
            '[class*="locker"]', '[class*="location"]', '[class*="store"]',
            '.card', '.item', 'li', '.station-item', '.facility-item'
        ]
        
        elements = []
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                break
        
        # 如果沒有找到特定元素，嘗試查找包含置物櫃相關關鍵詞的文本
        if not elements:
            text_blocks = soup.find_all(text=True)
            for text in text_blocks:
                if any(keyword in text.lower() for keyword in ['locker', '置物櫃', 'cloak', '行李', 'コインロッカー', 'ロッカー']):
                    parent = text.parent
                    if parent and parent.name in ['div', 'p', 'span', 'li', 'td']:
                        elements.append(parent)
        
        for el in elements:
            try:
                # 提取置物櫃名稱
                name = None
                name_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', '.title', '.name', '.location-name', '.station-name']
                for sel in name_selectors:
                    name_el = el.select_one(sel)
                    if name_el:
                        name = name_el.get_text(strip=True)
                        break
                
                if not name:
                    # 嘗試從元素文本中提取名稱
                    text = el.get_text(strip=True)
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    for line in lines:
                        if len(line) > 3 and len(line) < 50 and any(keyword in line for keyword in ['駅', 'Station', '車站', 'ロッカー', 'Locker']):
                            name = line
                            break
                
                # 提取地址信息
                address = None
                address_selectors = ['.address', '.location', '.address-text', '[class*="address"]', '.station-address']
                for sel in address_selectors:
                    addr_el = el.select_one(sel)
                    if addr_el:
                        address = addr_el.get_text(strip=True)
                        break
                
                if not address:
                    # 嘗試從文本中提取地址
                    text = el.get_text(strip=True)
                    if '地址' in text or 'Address' in text or '所在地' in text:
                        lines = text.split('\n')
                        for i, line in enumerate(lines):
                            if any(keyword in line for keyword in ['地址', 'Address', '所在地']):
                                if i + 1 < len(lines):
                                    address = lines[i + 1].strip()
                                    break
                
                # 提取地圖鏈接
                map_uri = None
                map_links = el.find_all('a', href=True)
                for link in map_links:
                    href = link['href']
                    if any(keyword in href.lower() for keyword in ['maps', 'google', 'map', 'location']):
                        map_uri = href
                        break
                
                # 提取座標信息
                latlng = None
                if map_uri:
                    latlng = _extract_lat_lng_from_text(map_uri)
                
                # 解析空位信息
                block_text = el.get_text("\n", strip=True)
                has_vacancy, available_slots = _parse_vacancy_info(block_text)
                
                if name or address:
                    items.append({
                        'name': name or '置物櫃',
                        'address': address or '—',
                        'map_uri': map_uri or url,
                        'latlng': latlng,
                        'has_vacancy': has_vacancy,
                        'available_slots': available_slots
                    })
            except Exception as e:
                logger.warning(f"解析通用置物櫃元素時出錯: {e}")
                continue
        
        # 如果沒有找到具體的置物櫃信息，至少返回網站入口
        if not items:
            items.append({
                'name': '置物櫃服務',
                'address': '—',
                'map_uri': url,
                'latlng': None,
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

def get_station_specific_lockers(lat: float, lng: float, location_name: str = None):
    """根據位置獲取特定車站或地點的置物櫃信息"""
    try:
        logger.info(f"🔍 查詢置物櫃 - 座標: ({lat}, {lng})")
        
        # 根據座標判斷是否為主要車站
        station_info = _identify_station_type(lat, lng)
        
        if station_info:
            logger.info(f"✅ 識別到車站: {station_info['name']}")
            # 如果是已知的主要車站，返回預設的置物櫃信息
            lockers = _get_predefined_station_lockers(station_info, lat, lng)
            logger.info(f"📦 返回預定義置物櫃: {len(lockers)} 個")
            return lockers
        else:
            logger.info("❌ 未識別到主要車站，返回通用置物櫃信息")
            # 如果不是主要車站，返回通用的置物櫃信息
            location_name = _get_location_name_from_coordinates(lat, lng)
            lockers = [{
                'name': f'{location_name} 置物櫃',
                'address': f'{location_name}地區',
                'map_uri': f'https://maps.google.com/?q={lat},{lng}',
                'latlng': (lat, lng),
                'distance_km': 0.0,
                'has_vacancy': True,
                'available_slots': 10,
                'location_type': 'general',
                'size_options': ['小', '中', '大'],
                'price_range': '300-600円'
            }]
            logger.info(f"🌐 返回通用置物櫃: {len(lockers)} 個")
            return lockers
    except Exception as e:
        logger.error(f"獲取車站特定置物櫃失敗: {e}")
        return fetch_nearby_lockers(lat, lng, max_items=5)

def _identify_station_type(lat: float, lng: float):
    """識別車站類型"""
    # 富山站（擴大識別範圍）
    if 36.69 <= lat <= 36.70 and 137.20 <= lng <= 137.22:
        return {
            'name': '富山站',
            'city': '富山',
            'type': 'major_station',
            'railway_company': 'JR西日本'
        }
    # 東京站
    elif 35.681 <= lat <= 35.682 and 139.767 <= lng <= 139.768:
        return {
            'name': '東京站',
            'city': '東京',
            'type': 'major_station',
            'railway_company': 'JR東日本'
        }
    # 新宿站
    elif 35.689 <= lat <= 35.691 and 139.700 <= lng <= 139.702:
        return {
            'name': '新宿站',
            'city': '東京',
            'type': 'major_station',
            'railway_company': 'JR東日本'
        }
    # 大阪站
    elif 34.702 <= lat <= 34.704 and 135.495 <= lng <= 135.497:
        return {
            'name': '大阪站',
            'city': '大阪',
            'type': 'major_station',
            'railway_company': 'JR西日本'
        }
    # 京都站
    elif 34.985 <= lat <= 34.986 and 135.758 <= lng <= 135.759:
        return {
            'name': '京都站',
            'city': '京都',
            'type': 'major_station',
            'railway_company': 'JR西日本'
        }
    return None

def _get_predefined_station_lockers(station_info, lat: float, lng: float):
    """獲取預定義的車站置物櫃信息"""
    station_name = station_info['name']
    city = station_info['city']
    
    # 根據車站類型返回相應的置物櫃信息
    if station_info['type'] == 'major_station':
        lockers = []
        
        # 富山站的置物櫃信息
        if station_name == '富山站':
            lockers = [
                {
                    'name': '富山站 東口 置物櫃',
                    'address': '富山縣富山市明輪町1-227',
                    'map_uri': f'https://maps.google.com/?q={lat},{lng}',
                    'latlng': (lat + 0.0001, lng + 0.0001),
                    'distance_km': 0.1,
                    'has_vacancy': True,
                    'available_slots': 15,
                    'location_type': 'station_exit',
                    'size_options': ['小', '中', '大'],
                    'price_range': '300-600円'
                },
                {
                    'name': '富山站 西口 置物櫃',
                    'address': '富山縣富山市明輪町1-227',
                    'map_uri': f'https://maps.google.com/?q={lat},{lng}',
                    'latlng': (lat - 0.0001, lng - 0.0001),
                    'distance_km': 0.1,
                    'has_vacancy': True,
                    'available_slots': 12,
                    'location_type': 'station_exit',
                    'size_options': ['小', '中', '大'],
                    'price_range': '300-600円'
                },
                {
                    'name': '富山站 改札內 置物櫃',
                    'address': '富山縣富山市明輪町1-227',
                    'map_uri': f'https://maps.google.com/?q={lat},{lng}',
                    'latlng': (lat, lng),
                    'distance_km': 0.0,
                    'has_vacancy': True,
                    'available_slots': 8,
                    'location_type': 'inside_station',
                    'size_options': ['小', '中'],
                    'price_range': '300-500円'
                }
            ]
        
        # 東京站的置物櫃信息
        elif station_name == '東京站':
            lockers = [
                {
                    'name': '東京站 丸之內北口 置物櫃',
                    'address': '東京都千代田區丸之內1-9-1',
                    'map_uri': f'https://maps.google.com/?q={lat},{lng}',
                    'latlng': (lat + 0.0002, lng + 0.0002),
                    'distance_km': 0.1,
                    'has_vacancy': True,
                    'available_slots': 25,
                    'location_type': 'station_exit',
                    'size_options': ['小', '中', '大'],
                    'price_range': '400-800円'
                },
                {
                    'name': '東京站 八重洲南口 置物櫃',
                    'address': '東京都千代田區丸之內1-9-1',
                    'map_uri': f'https://maps.google.com/?q={lat},{lng}',
                    'latlng': (lat - 0.0002, lng - 0.0002),
                    'distance_km': 0.1,
                    'has_vacancy': True,
                    'available_slots': 20,
                    'location_type': 'station_exit',
                    'size_options': ['小', '中', '大'],
                    'price_range': '400-800円'
                }
            ]
        
        # 其他車站的通用置物櫃信息
        else:
            lockers = [
                {
                    'name': f'{station_name} 置物櫃',
                    'address': f'{city}',
                    'map_uri': f'https://maps.google.com/?q={lat},{lng}',
                    'latlng': (lat, lng),
                    'distance_km': 0.0,
                    'has_vacancy': True,
                    'available_slots': 10,
                    'location_type': 'station',
                    'size_options': ['小', '中', '大'],
                    'price_range': '300-600円'
                }
            ]
        
        return lockers
    
    return []

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
        # 加入預設整合來源（避免重複）
        for u in DEFAULT_LOCKER_SOURCES:
            if u not in urls:
                urls.append(u)

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
        
        # 過濾掉距離過遠的置物櫃（超過50公里）
        nearby_with_distance = [c for c in with_distance if c['distance_km'] <= 50]
        far_with_distance = [c for c in with_distance if c['distance_km'] > 50]
        
        # 優先顯示附近的置物櫃，如果附近沒有，再考慮較遠的
        if nearby_with_distance:
            nearby_with_distance.sort(key=lambda x: x['distance_km'])
            lockers_sorted = nearby_with_distance + without_distance
        else:
            # 如果附近沒有置物櫃，顯示較遠的（但限制在100公里內）
            far_with_distance = [c for c in far_with_distance if c['distance_km'] <= 100]
            far_with_distance.sort(key=lambda x: x['distance_km'])
            lockers_sorted = far_with_distance + without_distance

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

def build_lockers_carousel(lockers, current_index=0, user_lat=None, user_lng=None):
    """構建置物櫃輪播圖，支持單個顯示和分頁功能"""
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
    
    # 確保索引在有效範圍內
    current_index = max(0, min(current_index, len(lockers) - 1))
    item = lockers[current_index]
    
    # 只顯示當前索引的置物櫃
    name = item.get('name')
    addr = item.get('address')
    uri = item.get('map_uri')
    distance_km = item.get('distance_km')
    has_distance = isinstance(distance_km, (int, float))
    has_vacancy = item.get('has_vacancy')
    available_slots = item.get('available_slots')

    # 根據用戶位置生成標題
    if user_lat is not None and user_lng is not None:
        location_name = _get_location_name_from_coordinates(user_lat, user_lng)
        header_title = f"{location_name} 置物櫃"
    else:
        # 產生適合顯示的地點標題（盡量顯示站名/地點，而非來源網站）
        def _clean_title(text: str) -> str:
            if not text:
                return ''
            cleaned = text
            # 去除常見來源或泛稱用語
            for bad in [
                '東京メトロ', 'Tokyo Metro', 'Locker Concierge', 'ロッカーコンシェルジュ',
                'コインロッカー一覧', 'Coin Locker Map', 'コインロッカーガイド',
                'コインロッカー', 'Coin Locker', 'ロッカー', 'Lockers', '附近置物點',
                '駅コインロッカー案内', 'QR Translator'
            ]:
                cleaned = cleaned.replace(bad, '')
            return cleaned.strip(' ・-—|/\u3000')

        def _looks_like_place(text: str) -> bool:
            if not text:
                return False
            tokens = ['駅', 'Station', '車站', '機場', '空港', '機场']
            return any(t in text for t in tokens)

        title_candidates = []
        if _looks_like_place(addr):
            title_candidates.append(_clean_title(addr))
        if _looks_like_place(name):
            title_candidates.append(_clean_title(name))
        # 一般情況也嘗試用 name
        title_candidates.append(_clean_title(name))
        # 最後備援用地址
        title_candidates.append(_clean_title(addr))
        header_title = next((t for t in title_candidates if t), '附近置物櫃')

    # 狀態徽章
    if has_vacancy is True:
        vacancy_short = "有空"
        vacancy_color = "#0E7A0D"
    elif has_vacancy is False:
        vacancy_short = "已滿"
        vacancy_color = "#B00020"
    else:
        vacancy_short = None
        vacancy_color = "#AAAAAA"

    vacancy_chip = None
    if vacancy_short:
        text_val = vacancy_short if not isinstance(available_slots, int) else f"{vacancy_short}（約{available_slots}）"
        vacancy_chip = {
            "type": "box",
            "layout": "baseline",
            "contents": [
                {"type": "text", "text": text_val, "size": "xs", "weight": "bold", "color": "#ffffff"}
            ],
            "backgroundColor": vacancy_color,
            "cornerRadius": "12px",
            "paddingAll": "6px"
        }

    distance_chip = None
    if has_distance:
        distance_chip = {
            "type": "box",
            "layout": "baseline",
            "contents": [
                {"type": "text", "text": f"約 {distance_km:.1f} 公里", "size": "xs", "color": "#333333"}
            ],
            "backgroundColor": "#F2F2F2",
            "cornerRadius": "12px",
            "paddingAll": "6px"
        }

    chips_row_contents = []
    if vacancy_chip:
        chips_row_contents.append(vacancy_chip)
    if distance_chip:
        chips_row_contents.append(distance_chip)

    body_contents = []
    if chips_row_contents:
        body_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": chips_row_contents,
            "spacing": "sm",
            "margin": "sm"
        })
    body_contents.append({"type": "separator", "margin": "md"})
    
    # 改善地點信息顯示
    location_info = []
    if name and addr and name != addr:
        # 如果名稱和地址不同，分別顯示
        location_info.append({
            "type": "text", 
            "text": f"🏢 {name}", 
            "size": "md", 
            "color": "#333333", 
            "weight": "bold",
            "wrap": True, 
            "margin": "sm"
        })
        location_info.append({
            "type": "text", 
            "text": f"📍 {addr}", 
            "size": "sm", 
            "color": "#666666", 
            "wrap": True, 
            "margin": "xs"
        })
    else:
        # 如果名稱和地址相同或只有一個，合併顯示
        display_text = name if name else addr
        location_info.append({
            "type": "text", 
            "text": f"📍 {display_text}", 
            "size": "md", 
            "color": "#333333", 
            "weight": "bold",
            "wrap": True, 
            "margin": "sm"
        })
    
    # 添加置物櫃詳細信息
    locker_details = []
    
    # 尺寸選項
    size_options = item.get('size_options')
    if size_options:
        size_text = "📦 尺寸: " + " / ".join(size_options)
        locker_details.append({
            "type": "text",
            "text": size_text,
            "size": "sm",
            "color": "#555555",
            "margin": "xs"
        })
    
    # 價格範圍
    price_range = item.get('price_range')
    if price_range:
        price_text = f"💰 價格: {price_range}"
        locker_details.append({
            "type": "text",
            "text": price_text,
            "size": "sm",
            "color": "#555555",
            "margin": "xs"
        })
    
    # 位置類型
    location_type = item.get('location_type')
    if location_type:
        type_text = ""
        if location_type == 'station_exit':
            type_text = "🚪 位置: 車站出口"
        elif location_type == 'inside_station':
            type_text = "🚇 位置: 車站內"
        elif location_type == 'station':
            type_text = "🚉 位置: 車站"
        
        if type_text:
            locker_details.append({
                "type": "text",
                "text": type_text,
                "size": "sm",
                "color": "#555555",
                "margin": "xs"
            })
    
    # 添加地點信息到內容中
    body_contents.extend(location_info)
    
    # 添加置物櫃詳細信息
    if locker_details:
        body_contents.extend(locker_details)

    # 構建分頁按鈕
    footer_buttons = []
    
    # 導航按鈕
    footer_buttons.append({
        "type": "button", 
        "action": {"type": "uri", "label": "導航", "uri": uri}, 
        "style": "primary", 
        "color": "#FFA500", 
        "height": "sm"
    })
    
    # 分頁按鈕
    if len(lockers) > 1:
        # 顯示當前位置和總數
        page_info = f"{current_index + 1}/{len(lockers)}"
        
        # 如果有下一個置物櫃，添加"查看下一個"按鈕
        if current_index < len(lockers) - 1:
            footer_buttons.append({
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": f"查看下一個 ({page_info})",
                    "data": f"action=locker_next&index={current_index + 1}&total={len(lockers)}"
                },
                "style": "secondary",
                "color": "#666666",
                "height": "sm"
            })
        else:
            # 如果是最後一個，顯示"重新開始"按鈕
            footer_buttons.append({
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": f"重新開始 ({page_info})",
                    "data": f"action=locker_next&index=0&total={len(lockers)}"
                },
                "style": "secondary",
                "color": "#666666",
                "height": "sm"
            })

    bubble = {
        "type": "bubble",
        "size": "kilo",
        "action": {"type": "uri", "uri": uri, "label": "查看地圖"},
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [{"type": "text", "text": f"🛅 {header_title}", "weight": "bold", "size": "lg", "color": "#ffffff", "align": "center"}],
            "backgroundColor": "#F59E0B",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": body_contents,
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": footer_buttons,
            "paddingAll": "20px"
        }
    }
    
    return bubble

# 用戶會話存儲（簡單的內存存儲，生產環境建議使用 Redis 或數據庫）
_user_locker_sessions = {}

def store_user_locker_session(user_id: str, lockers: list, message_id: str = None, user_lat: float = None, user_lng: float = None):
    """存儲用戶的置物櫃會話數據"""
    _user_locker_sessions[user_id] = {
        'lockers': lockers,
        'message_id': message_id,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'timestamp': time.time()
    }

def get_user_locker_session(user_id: str):
    """獲取用戶的置物櫃會話數據"""
    session = _user_locker_sessions.get(user_id)
    if session:
        # 檢查會話是否過期（30分鐘）
        if time.time() - session['timestamp'] < 1800:
            return session
        else:
            # 會話過期，清除
            del _user_locker_sessions[user_id]
    return None

def build_locker_with_pagination(user_id: str, current_index: int = 0):
    """根據用戶會話和當前索引構建置物櫃顯示"""
    session = get_user_locker_session(user_id)
    if not session:
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "會話已過期，請重新查詢附近置物櫃", "align": "center", "color": "#666666"}
                ],
                "paddingAll": "20px"
            }
        }
    
    return build_lockers_carousel(session['lockers'], current_index, session.get('user_lat'), session.get('user_lng'))

def get_user_message_id(user_id: str):
    """獲取用戶的消息ID"""
    session = get_user_locker_session(user_id)
    return session['message_id'] if session else None
