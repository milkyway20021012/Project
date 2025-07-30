# 消息模板配置
MESSAGE_TEMPLATES = {
    "reminder": {
        "10_min_before": {
            "emoji": "⏰",
            "title": "集合提醒",
            "message": "還有 10 分鐘就要集合了！",
            "color": "#F39C12"
        },
        "5_min_before": {
            "emoji": "🚨",
            "title": "緊急提醒",
            "message": "還有 5 分鐘就要集合了！",
            "color": "#E74C3C"
        },
        "on_time": {
            "emoji": "🎯",
            "title": "集合時間到了！",
            "message": "集合時間到了！請準時到達！",
            "color": "#E74C3C"
        }
    },
    "features": {
        "leaderboard": {
            "title": "🏆 排行榜",
            "description": "查看最新的排行榜",
            "sub_description": "點擊下方按鈕查看詳細排名",
            "button_text": "查看排行榜",
            "color": "#FF6B6B",
            "url": "https://tourhub-ashy.vercel.app/?state=n6sFheuU2eAl&liffClientId=2007678368&liffRedirectUri=https%3A%2F%2Ftourhub-ashy.vercel.app%2F&code=DJhtwXyqmCdyhnBlGs3s"
        },
        "trip_management": {
            "title": "🗓️ 行程管理",
            "description": "建立屬於您的專屬行程內容",
            "sub_description": "點擊下方按鈕開始規劃您的完美旅程",
            "button_text": "管理行程",
            "color": "#4ECDC4",
            "url": "https://tripfrontend.vercel.app/linetrip"
        },
        "locker": {
            "title": "🛅 置物櫃",
            "description": "快速定位附近有空位的置物櫃",
            "sub_description": "輕鬆寄存行李，讓您的旅程更輕鬆",
            "button_text": "尋找置物櫃",
            "color": "#FFA500",
            "url": "https://tripfrontend.vercel.app/linelocker"
        },
        "split_bill": {
            "title": "💰 分帳工具",
            "description": "記錄每一筆費用，自動計算每人應付金額",
            "sub_description": "輕鬆分攤旅費，避免尷尬的算帳時刻",
            "button_text": "開始分帳",
            "color": "#28A745",
            "url": "https://liff.line.me/2007317887-Dq8Rorg5"
        },
        "tourclock": {
            "title": "⏰ TourClock",
            "description": "智能集合時間管理工具",
            "sub_description": "設定集合時間，自動發送提醒通知",
            "button_text": "開啟 TourClock",
            "color": "#9B59B6",
            "url": "https://tourclock.vercel.app"
        }
    },
    "meeting_success": {
        "title": "📍 集合設定成功",
        "color": "#9B59B6",
        "status_success": "已同步到 TourClock",
        "status_success_color": "#27AE60",
        "status_local": "本地設定",
        "status_local_color": "#F39C12",
        "reminder_info": "⏰ 智能提醒設定",
        "reminder_details": "• 集合前 10 分鐘提醒\n• 集合前 5 分鐘提醒\n• 集合時間到提醒"
    },
    "help": {
        "title": "📱 TourHub 功能介紹",
        "color": "#6C5CE7",
        "features": [
            {
                "emoji": "🏆",
                "name": "排行榜 (Ranking List)",
                "description": "提供其他使用者的行程資訊進行排行，幫助您做行程規劃"
            },
            {
                "emoji": "🗓️",
                "name": "行程管理 (Trip Management)",
                "description": "建立屬於您的專屬行程內容"
            },
            {
                "emoji": "📍",
                "name": "集合功能 (Meeting Point)",
                "description": "設定集合地點，方便分散活動後重新集合"
            },
            {
                "emoji": "🛅",
                "name": "置物櫃 (Locker)",
                "description": "快速定位附近有空位的置物櫃，輕鬆寄存行李"
            },
            {
                "emoji": "💰",
                "name": "分帳工具 (Split Bill)",
                "description": "記錄每一筆費用，自動計算每人應付金額"
            },
        ]
    }
}

# 排行榜數據配置
LEADERBOARD_DATA = {
    "1": {
        "title": "🥇 排行榜第一名",
        "color": "#FFD700",
        "destination": "東京",
        "duration": "5天4夜",
        "participants": "4人",
        "feature": "經典關東地區深度遊",
        "itinerary": "Day 1: 淺草寺 → 晴空塔 → 秋葉原\nDay 2: 明治神宮 → 原宿 → 澀谷\nDay 3: 新宿 → 池袋 → 銀座\nDay 4: 台場 → 築地市場 → 東京鐵塔\nDay 5: 上野公園 → 阿美橫町 → 機場"
    },
    "2": {
        "title": "🥈 排行榜第二名",
        "color": "#C0C0C0",
        "destination": "大阪",
        "duration": "4天3夜",
        "participants": "3人",
        "feature": "關西美食文化之旅",
        "itinerary": "Day 1: 大阪城 → 道頓堀 → 心齋橋\nDay 2: 環球影城一日遊\nDay 3: 天保山摩天輪 → 海遊館 → 梅田藍天大廈\nDay 4: 通天閣 → 新世界 → 機場"
    },
    "3": {
        "title": "🥉 排行榜第三名",
        "color": "#CD7F32",
        "destination": "京都",
        "duration": "6天5夜",
        "participants": "2人",
        "feature": "古都文化深度體驗",
        "itinerary": "Day 1: 金閣寺 → 龍安寺 → 二条城\nDay 2: 清水寺 → 地主神社 → 祇園\nDay 3: 伏見稻荷大社 → 東福寺 → 三十三間堂\nDay 4: 嵐山竹林 → 天龍寺 → 渡月橋\nDay 5: 銀閣寺 → 哲學之道 → 南禪寺\nDay 6: 西陣織會館 → 機場"
    },
    "4": {
        "title": "🏅 排行榜第四名",
        "color": "#4ECDC4",
        "destination": "沖繩",
        "duration": "5天4夜",
        "participants": "5人",
        "feature": "海島度假放鬆之旅",
        "itinerary": "Day 1: 首里城 → 國際通 → 牧志公設市場\nDay 2: 美麗海水族館 → 古宇利島 → 名護鳳梨園\nDay 3: 萬座毛 → 真榮田岬 → 殘波岬\nDay 4: 座喜味城跡 → 讀谷村 → 北谷町美國村\nDay 5: 瀨長島 → 機場"
    },
    "5": {
        "title": "🎖️ 排行榜第五名",
        "color": "#FF6B9D",
        "destination": "北海道",
        "duration": "7天6夜",
        "participants": "6人",
        "feature": "北國風情深度探索",
        "itinerary": "Day 1: 札幌市區 → 大通公園 → 狸小路商店街\nDay 2: 小樽運河 → 小樽音樂盒堂 → 北一硝子\nDay 3: 函館山夜景 → 五稜郭公園 → 元町異人館\nDay 4: 富良野薰衣草田 → 美瑛青池 → 白金溫泉\nDay 5: 洞爺湖 → 昭和新山 → 登別溫泉\nDay 6: 旭山動物園 → 層雲峽 → 大雪山\nDay 7: 機場"
    }
}

# 關鍵字映射配置
KEYWORD_MAPPINGS = {
    "leaderboard": {
        "keywords": ["排行榜", "排名", "排行", "top", "Top", "leaderboard", "Leaderboard", "排名榜", "熱門", "熱門排行"],
        "template": "feature",
        "feature_name": "leaderboard"
    },
    "leaderboard_1": {
        "keywords": ["排行榜第一", "排行第一", "第一名", "top1", "Top1", "冠軍", "排行榜冠軍", "排行榜第一名"],
        "template": "leaderboard",
        "rank": "1"
    },
    "leaderboard_2": {
        "keywords": ["第二名", "排行第二", "top2", "Top2", "亞軍", "排行榜亞軍", "排行榜第二名"],
        "template": "leaderboard",
        "rank": "2"
    },
    "leaderboard_3": {
        "keywords": ["第三名", "排行第三", "top3", "Top3", "季軍", "排行榜季軍", "排行榜第三名"],
        "template": "leaderboard",
        "rank": "3"
    },
    "leaderboard_4": {
        "keywords": ["第四名", "排行第四", "top4", "Top4", "排行榜第四名"],
        "template": "leaderboard",
        "rank": "4"
    },
    "leaderboard_5": {
        "keywords": ["第五名", "排行第五", "top5", "Top5", "排行榜第五名"],
        "template": "leaderboard",
        "rank": "5"
    },
    "trip_management": {
        "keywords": ["行程管理", "行程", "旅遊", "旅行", "規劃", "計劃", "行程規劃", "旅遊規劃", "trip", "Trip", "travel", "Travel", "schedule", "Schedule", "plan", "Plan", "行程表", "旅遊行程"],
        "template": "feature",
        "feature_name": "trip_management"
    },
    "locker": {
        "keywords": ["置物櫃", "寄物點", "行李寄存", "寄物", "置物", "locker", "Locker"],
        "template": "feature",
        "feature_name": "locker"
    },
    "split_bill": {
        "keywords": ["分帳", "AA", "平分", "均分", "分錢", "算帳", "結帳", "付款", "付錢", "share", "Share", "split", "Split"],
        "template": "feature",
        "feature_name": "split_bill"
    },
    "tourclock": {
        "keywords": ["集合", "集合點", "集合地點", "集合時間", "meeting", "Meeting", "meet", "Meet", "gather", "Gather", "集合管理", "時間管理", "提醒", "tourclock", "TourClock", "Tourclock"],
        "template": "feature",
        "feature_name": "tourclock"
    },
    "help": {
        "keywords": ["功能介紹", "功能", "介紹", "說明", "help", "Help", "功能說明", "使用說明","Tourhub功能介紹","Tourhub功能","Tourhub介紹","Tourhub說明"],
        "template": "help"
    }
}

# 集合地點配置
MEETING_LOCATIONS = [
    "東京鐵塔", "淺草寺", "新宿車站", "澀谷", "銀座", "秋葉原", "原宿", "池袋", "台場", "築地市場", 
    "上野公園", "阿美橫町", "大阪城", "道頓堀", "心齋橋", "環球影城", "天保山", "海遊館", "梅田", 
    "通天閣", "新世界", "金閣寺", "龍安寺", "二条城", "清水寺", "地主神社", "祇園", "伏見稻荷大社", 
    "東福寺", "三十三間堂", "嵐山", "天龍寺", "渡月橋", "銀閣寺", "哲學之道", "南禪寺", "西陣織會館", 
    "首里城", "國際通", "牧志公設市場", "美麗海水族館", "古宇利島", "名護鳳梨園", "萬座毛", "真榮田岬", 
    "殘波岬", "座喜味城跡", "讀谷村", "北谷町美國村", "瀨長島", "札幌", "大通公園", "狸小路商店街", 
    "小樽運河", "小樽音樂盒堂", "北一硝子", "函館山", "五稜郭公園", "元町異人館", "富良野", "美瑛青池", 
    "白金溫泉", "洞爺湖", "昭和新山", "登別溫泉", "旭山動物園", "層雲峽", "大雪山"
]

# 時間解析模式
TIME_PATTERNS = {
    "standard": r'(\d{1,2}:\d{2})',
    "chinese": r'(\d{1,2})點(\d{1,2})分',
    "simple_chinese": r'(\d{1,2})點',
    "am_pm": r'(上午|下午|晚上|凌晨)\s*(\d{1,2})[點:](\d{1,2})?'
}

# 集合時間模式
MEETING_TIME_PATTERN = r'集合.*時間|時間.*集合|集合.*\d{1,2}:\d{2}|明天.*集合|今天.*集合|下午.*集合|上午.*集合|晚上.*集合|凌晨.*集合|集合.*下午|集合.*上午|集合.*晚上|集合.*凌晨|\d{1,2}:\d{2}.*集合|\d{1,2}點\d{1,2}分.*集合|\d{1,2}點.*集合'

# 行程資料庫已移除，改為從資料庫動態獲取 