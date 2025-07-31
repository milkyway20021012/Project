# Vercel 部署錯誤修復

## 🐛 錯誤分析

您遇到的錯誤：
```
TypeError: issubclass() arg 1 must be a class
```

這是 Vercel Python 運行時的兼容性問題，通常由以下原因造成：

1. **Flask 版本問題**：Flask 3.0.0 與 Vercel 的 Python 運行時不完全兼容
2. **WSGI 處理問題**：Vercel 對 WSGI 應用的處理方式有特定要求
3. **依賴衝突**：某些依賴包可能與 Vercel 環境衝突

## ✅ 修復措施

### 1. 降級 Flask 版本
```diff
- flask==3.0.0
+ flask==2.3.3
```

### 2. 簡化依賴
移除了不必要的依賴：
```diff
- beautifulsoup4==4.12.2
- mysql-connector-python==9.4.0
- pymysql==1.1.1
```

### 3. 優化 Vercel 配置
確保 `vercel.json` 正確指向主要文件：
```json
{
    "version": 2,
    "builds": [
        {
            "src": "api/index.py",
            "use": "@vercel/python"
        }
    ],
    "routes": [
        {
            "src": "/(.*)",
            "dest": "/api/index.py"
        }
    ]
}
```

### 4. 簡化入口點
移除了複雜的 handler 函數，讓 Vercel 直接使用 Flask app：
```python
# Vercel 會自動檢測名為 'app' 的 Flask 實例
# 確保 app 在模組級別可用
```

## 🚀 部署步驟

1. **重新部署**：
   ```bash
   vercel --prod
   ```

2. **檢查狀態**：
   - 訪問 `https://你的域名.vercel.app/` 
   - 應該看到：`{"status": "running", "bot_configured": true}`

3. **測試功能**：
   - 在 Line 中發送：`下午2:35 淺草寺集合`
   - 應該收到美觀的 Flex Message 回應

## 📋 當前配置

### requirements.txt
```
flask==2.3.3
line-bot-sdk==3.7.0
requests==2.31.0
```

### 核心功能
- ✅ 時間解析（多種格式）
- ✅ 地點解析（智能識別）
- ✅ Flex Message 生成
- ✅ 集合設定確認
- ✅ 提醒時間計算

### Vercel 兼容性
- ✅ 無狀態設計
- ✅ 簡化依賴
- ✅ 標準 WSGI 接口
- ✅ 環境變數支援

## 🔍 故障排除

如果仍有問題：

1. **檢查 Vercel 日誌**：
   ```bash
   vercel logs
   ```

2. **驗證環境變數**：
   - `CHANNEL_ACCESS_TOKEN`
   - `CHANNEL_SECRET`

3. **測試基本端點**：
   - `/` - 健康檢查
   - `/debug` - 環境變數檢查
   - `/callback` - Line Bot webhook

## 📞 支援

如果問題持續存在，請提供：
- Vercel 部署日誌
- 錯誤訊息截圖
- Line Bot 設定截圖

## 🎉 預期結果

修復後，您的 Line Bot 應該能夠：
- 正常接收和回應訊息
- 解析集合時間和地點
- 生成美觀的 Flex Message
- 提供智能提醒時間表

立即測試：在 Line 中輸入 `下午2:35 淺草寺集合`！
