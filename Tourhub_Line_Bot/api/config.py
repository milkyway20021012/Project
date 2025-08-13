# 消息模板配置
MESSAGE_TEMPLATES = {
    # 集合提醒模板已移除
    "features": {
        "leaderboard": {
            "title": "🏆 排行榜",
            "description": "查看最新的排行榜",
            "sub_description": "點擊下方按鈕查看詳細排名",
            "button_text": "查看排行榜",
            "color": "#FF6B6B",
            "url": "https://tourhub-ashy.vercel.app/"
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
        "tour_clock": {
            "title": "⏰ TourClock",
            "description": "智能集合時間管理工具",
            "sub_description": "設定集合時間，自動發送提醒通知",
            "button_text": "開啟 TourClock",
            "color": "#9B59B6",
            "url": "https://tourclock-dvf2.vercel.app/?state=EICy1YHneLoC&liffClientId=2007488134&liffRedirectUri=https%3A%2F%2Ftourclock-dvf2.vercel.app&code=uj41KyebQrmS2IzWredf"
        }
    },
    # 集合成功模板已移除
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
                "emoji": "⏰",
                "name": "集合管理 (TourClock)",
                "description": "智能集合時間管理工具，設定集合時間並自動發送提醒"
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
    },

    # 功能選單模板
    "feature_menu": {
        "title": "🎯 選擇您想了解的功能",
        "color": "#6C5CE7",
        "description": "點擊下方按鈕查看詳細功能介紹"
    },

    # 功能詳細介紹模板
    "feature_details": {
        "leaderboard": {
            "title": "🏆 排行榜功能",
            "color": "#FF6B6B",
            "description": "查看最受歡迎的旅遊行程排行榜",
            "details": [
                "📊 即時更新的行程排名",
                "⭐ 根據用戶評分和收藏數排序",
                "🔍 可查看詳細行程內容",
                "💡 為您的旅行提供靈感"
            ],
            "usage_steps": [
                "1️⃣ 輸入「排行榜」查看完整排名",
                "2️⃣ 輸入「第一名」查看冠軍行程",
                "3️⃣ 輸入「第一名詳細行程」查看完整內容"
            ],
            "button_text": "立即查看排行榜",
            "url": "https://tourhub-ashy.vercel.app/"
        },
        "trip_management": {
            "title": "🗓️ 行程管理功能",
            "color": "#4ECDC4",
            "description": "建立和管理您的專屬旅遊行程",
            "details": [
                "📝 自由建立個人行程",
                "📅 靈活安排時間和地點",
                "🔄 隨時修改和更新",
                "📱 手機電腦同步使用"
            ],
            "usage_steps": [
                "1️⃣ 輸入「行程管理」開始使用",
                "2️⃣ 點擊按鈕進入管理頁面",
                "3️⃣ 建立您的專屬行程"
            ],
            "button_text": "開始管理行程",
            "url": "https://tripfrontend.vercel.app/linetrip"
        },
        "tour_clock": {
            "title": "⏰ 集合管理功能",
            "color": "#9B59B6",
            "description": "智能集合時間管理工具",
            "details": [
                "⏰ 設定集合時間和地點",
                "📢 自動發送提醒通知",
                "👥 管理團體集合狀況",
                "🔔 避免遲到和走失"
            ],
            "usage_steps": [
                "1️⃣ 輸入「集合」或「集合時間」",
                "2️⃣ 設定集合的時間和地點",
                "3️⃣ 系統會自動發送提醒"
            ],
            "button_text": "設定集合時間",
            "url": "https://tripfrontend.vercel.app/linetourclock"
        },
        "locker": {
            "title": "🛅 置物櫃功能",
            "color": "#FFA500",
            "description": "快速找到附近的置物櫃服務",
            "details": [
                "📍 定位附近置物櫃位置",
                "✅ 即時查看空位狀況",
                "💰 比較不同價格方案",
                "🎒 輕鬆寄存行李物品"
            ],
            "usage_steps": [
                "1️⃣ 輸入「置物櫃」或「寄物」",
                "2️⃣ 點擊按鈕查看附近位置",
                "3️⃣ 選擇合適的置物櫃"
            ],
            "button_text": "尋找置物櫃",
            "url": "https://tripfrontend.vercel.app/linelocker"
        },
        "split_bill": {
            "title": "💰 分帳工具功能",
            "color": "#E74C3C",
            "description": "輕鬆管理旅行中的共同費用",
            "details": [
                "💳 記錄每筆旅行支出",
                "🧮 自動計算分攤金額",
                "👥 支援多人分帳",
                "📊 清楚的費用明細"
            ],
            "usage_steps": [
                "1️⃣ 輸入「分帳」或「AA」",
                "2️⃣ 點擊按鈕開始記帳",
                "3️⃣ 輸入費用和分攤人數"
            ],
            "button_text": "開始分帳",
            "url": "https://tripfrontend.vercel.app/linesplitbill"
        }
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
        "template": "leaderboard_list"
    },
    "leaderboard_1": {
        "keywords": ["排行榜第一", "排行第一", "第一名", "top1", "Top1", "冠軍", "排行榜冠軍", "排行榜第一名"],
        "template": "leaderboard",
        "rank": "1"
    },
    "leaderboard_1_details": {
        "keywords": ["第一名詳細行程", "第一名行程", "第一名詳細", "冠軍詳細行程", "冠軍行程", "排行榜第一名詳細", "排行榜第一詳細行程", "top1詳細", "Top1詳細"],
        "template": "leaderboard_details",
        "rank": "1"
    },
    "leaderboard_2": {
        "keywords": ["第二名", "排行第二", "top2", "Top2", "亞軍", "排行榜亞軍", "排行榜第二名"],
        "template": "leaderboard",
        "rank": "2"
    },
    "leaderboard_2_details": {
        "keywords": ["第二名詳細行程", "第二名行程", "第二名詳細", "亞軍詳細行程", "亞軍行程", "排行榜第二名詳細", "top2詳細", "Top2詳細"],
        "template": "leaderboard_details",
        "rank": "2"
    },
    "leaderboard_3": {
        "keywords": ["第三名", "排行第三", "top3", "Top3", "季軍", "排行榜季軍", "排行榜第三名"],
        "template": "leaderboard",
        "rank": "3"
    },
    "leaderboard_3_details": {
        "keywords": ["第三名詳細行程", "第三名行程", "第三名詳細", "季軍詳細行程", "季軍行程", "排行榜第三名詳細", "top3詳細", "Top3詳細"],
        "template": "leaderboard_details",
        "rank": "3"
    },
    "leaderboard_4": {
        "keywords": ["第四名", "排行第四", "top4", "Top4", "排行榜第四名"],
        "template": "leaderboard",
        "rank": "4"
    },
    "leaderboard_4_details": {
        "keywords": ["第四名詳細行程", "第四名行程", "第四名詳細", "排行榜第四名詳細", "top4詳細", "Top4詳細"],
        "template": "leaderboard_details",
        "rank": "4"
    },
    "leaderboard_5": {
        "keywords": ["第五名", "排行第五", "top5", "Top5", "排行榜第五名"],
        "template": "leaderboard",
        "rank": "5"
    },
    "leaderboard_5_details": {
        "keywords": ["第五名詳細行程", "第五名行程", "第五名詳細", "排行榜第五名詳細", "top5詳細", "Top5詳細"],
        "template": "leaderboard_details",
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
    # TourClock集合功能
    "tour_clock": {
        "keywords": ["集合", "集合時間", "集合地點", "約時間", "約地點", "約見面", "見面", "會合", "聚集", "tour clock", "TourClock", "集合管理", "時間管理"],
        "template": "tour_clock"
    },

    # 地區行程查詢
    "tokyo_trips": {
        "keywords": ["東京", "東京行程", "東京旅遊", "東京景點", "tokyo", "Tokyo", "東京相關", "東京推薦"],
        "template": "location_trips",
        "location": "東京"
    },
    "osaka_trips": {
        "keywords": ["大阪", "大阪行程", "大阪旅遊", "大阪景點", "osaka", "Osaka", "大阪相關", "大阪推薦"],
        "template": "location_trips",
        "location": "大阪"
    },
    "kyoto_trips": {
        "keywords": ["京都", "京都行程", "京都旅遊", "京都景點", "kyoto", "Kyoto", "京都相關", "京都推薦"],
        "template": "location_trips",
        "location": "京都"
    },
    "okinawa_trips": {
        "keywords": ["沖繩", "沖繩行程", "沖繩旅遊", "沖繩景點", "okinawa", "Okinawa", "沖繩相關", "沖繩推薦"],
        "template": "location_trips",
        "location": "沖繩"
    },
    "hokkaido_trips": {
        "keywords": ["北海道", "北海道行程", "北海道旅遊", "北海道景點", "hokkaido", "Hokkaido", "北海道相關", "北海道推薦"],
        "template": "location_trips",
        "location": "北海道"
    },

    "help": {
        "keywords": ["功能介紹", "功能", "介紹", "說明", "help", "Help", "功能說明", "使用說明","Tourhub功能介紹","Tourhub功能","Tourhub介紹","Tourhub說明"],
        "template": "feature_menu"
    },

    # 功能詳細介紹關鍵字映射
    "leaderboard_detail_help": {
        "keywords": ["排行榜功能介紹", "排行榜說明", "排行榜怎麼用", "排行榜功能", "leaderboard help"],
        "template": "feature_detail",
        "feature_name": "leaderboard"
    },
    "trip_management_detail_help": {
        "keywords": ["行程管理功能介紹", "行程管理說明", "行程管理怎麼用", "行程管理功能", "trip management help"],
        "template": "feature_detail",
        "feature_name": "trip_management"
    },
    "tour_clock_detail_help": {
        "keywords": ["集合管理功能介紹", "集合功能介紹", "集合說明", "集合怎麼用", "TourClock功能介紹", "tour clock help"],
        "template": "feature_detail",
        "feature_name": "tour_clock"
    },
    "locker_detail_help": {
        "keywords": ["置物櫃功能介紹", "置物櫃說明", "置物櫃怎麼用", "寄物功能介紹", "locker help"],
        "template": "feature_detail",
        "feature_name": "locker"
    },
    "split_bill_detail_help": {
        "keywords": ["分帳功能介紹", "分帳說明", "分帳怎麼用", "AA功能介紹", "split bill help"],
        "template": "feature_detail",
        "feature_name": "split_bill"
    },

    "website_operations": {
        "keywords": ["網站操作", "操作網站", "使用網站", "網站功能", "我的操作"],
        "template": "website_operations"
    },
    # 獨立行程管理關鍵字已移除
    "view_trip": {
        "keywords": ["查看", "顯示行程", "行程內容"],
        "template": "view_trip"
    },
    "edit_trip": {
        "keywords": ["修改", "編輯", "更改標題", "改名"],
        "template": "edit_trip"
    },
    "delete_trip": {
        "keywords": ["刪除", "移除", "取消行程"],
        "template": "delete_trip"
    }
}

# 集合相關配置已移除

# 行程資料庫已移除，改為從資料庫動態獲取 