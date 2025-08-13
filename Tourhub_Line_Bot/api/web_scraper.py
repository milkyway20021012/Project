import requests
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

def scrape_leaderboard_data():
    """從 TourHub 網站抓取排行榜資料（無模擬內容）"""
    try:
        url = "https://tourhub-ashy.vercel.app/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找排行榜資料
        leaderboard_data = {}
        rank_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32", 4: "#4ECDC4", 5: "#FF6B9D"}
        rank_titles = {1: "🥇 第一名", 2: "🥈 第二名", 3: "🥉 第三名", 4: "🏅 第四名", 5: "🎖️ 第五名"}
        
        # 嘗試多種選擇器來找到排行榜項目
        selectors = [
            '.leaderboard-item',
            '.ranking-item', 
            '.trip-item',
            '[class*="rank"]',
            '[class*="leaderboard"]',
            '.card',
            '.item'
        ]
        
        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                logger.info(f"找到 {len(items)} 個項目使用選擇器: {selector}")
                break
        
        if not items:
            logger.warning("未找到排行榜項目")
            return {}
        
        # 解析找到的項目
        for i, item in enumerate(items[:5], 1):
            try:
                # 嘗試提取行程標題
                title_element = (
                    item.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or
                    item.find(class_=re.compile(r'title|name|heading', re.I)) or
                    item.find(['span', 'div'], text=re.compile(r'.+', re.I))
                )
                
                title = None
                if title_element:
                    title = title_element.get_text(strip=True)
                    # 清理標題
                    title = re.sub(r'^第?\d+名?[：:]?\s*', '', title)
                    title = re.sub(r'[🥇🥈🥉🏅🎖️]', '', title)
                
                # 嘗試提取地區資訊
                area = None
                area_keywords = ['日本', '東京', '大阪', '京都', '北海道', '沖繩', '名古屋', '福岡']
                if title:
                    for keyword in area_keywords:
                        if keyword in title:
                            area = keyword
                            break
                
                # 嘗試提取天數資訊
                duration = None
                duration_match = re.search(r'(\d+)天', (title or '') + str(item))
                if duration_match:
                    days = int(duration_match.group(1))
                    duration = f"{days}天{days-1}夜" if days > 1 else "1天"
                
                leaderboard_data[str(i)] = {
                    "rank": i,
                    "title": title or "",
                    "rank_title": rank_titles.get(i, f"第{i}名"),
                    "color": rank_colors.get(i, "#9B59B6"),
                    "destination": area or "",
                    "duration": duration or "",
                }
                
            except Exception as e:
                logger.error(f"解析第 {i} 個項目時出錯: {e}")
                continue
        
        logger.info(f"成功抓取 {len(leaderboard_data)} 筆排行榜資料")
        return leaderboard_data
        
    except Exception as e:
        logger.error(f"抓取網站資料失敗: {e}")
        return {}

def scrape_trip_details(rank):
    """從網站抓取特定排名的詳細行程（無模擬內容）"""
    try:
        url = "https://tourhub-ashy.vercel.app/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找詳細行程資料
        # 嘗試找到第 rank 個行程的詳細資訊
        detail_selectors = [
            f'.trip-detail-{rank}',
            f'[data-rank="{rank}"]',
            '.trip-details',
            '.itinerary',
            '.schedule'
        ]
        
        details_element = None
        for selector in detail_selectors:
            details_element = soup.select_one(selector)
            if details_element:
                break
        
        # 如果沒有找到特定的詳細資訊，直接返回 None
        if not details_element:
            logger.warning(f"未找到第{rank}名的詳細行程元素")
            return None

        # 嘗試拆出多行文字
        text = details_element.get_text("\n", strip=True)
        itinerary_lines = [line for line in text.split("\n") if line.strip()]

        rank_titles = {1: "🥇 第一名", 2: "🥈 第二名", 3: "🥉 第三名", 4: "🏅 第四名", 5: "🎖️ 第五名"}
        rank_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32", 4: "#4ECDC4", 5: "#FF6B9D"}

        result = {
            "rank": rank,
            "rank_title": rank_titles.get(rank, f"第{rank}名"),
            "title": "",
            "color": rank_colors.get(rank, "#9B59B6"),
            "area": "",
            "itinerary": "\n\n".join(itinerary_lines),
            "itinerary_list": itinerary_lines
        }

        logger.info(f"成功抓取第{rank}名的詳細行程文字，共 {len(itinerary_lines)} 行")
        return result
        
    except Exception as e:
        logger.error(f"抓取第{rank}名詳細行程失敗: {e}")
        return None

## 已移除預設排行榜模擬資料
