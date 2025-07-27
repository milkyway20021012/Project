# 🚨 Vercel 404 錯誤解決指南

## 🔍 問題診斷

您遇到的錯誤：
```
404: NOT_FOUND
Code: NOT_FOUND
ID: hkg1::8bpht-1753588593142-d1073cfbd4aa
```

這表示 Vercel 無法找到您請求的資源。

## 🛠️ 解決步驟

### 步驟 1：檢查部署狀態

1. 前往 [Vercel Dashboard](https://vercel.com/dashboard)
2. 選擇您的專案
3. 檢查部署狀態是否為 "Ready"
4. 如果部署失敗，查看錯誤日誌

### 步驟 2：檢查函數構建

1. 在 Vercel Dashboard 中點擊 **Functions** 標籤
2. 查看是否有 `app.py` 函數
3. 檢查函數狀態是否正常

### 步驟 3：測試基本端點

嘗試訪問以下端點：

```bash
# 基本端點
curl https://your-project.vercel.app/

# 測試端點
curl https://your-project.vercel.app/test

# 健康檢查
curl https://your-project.vercel.app/health
```

### 步驟 4：常見原因及解決方案

#### 原因 1：部署失敗
**症狀**：函數未正確構建
**解決方案**：
- 檢查 Vercel 部署日誌
- 確保所有依賴都已安裝
- 重新部署專案

#### 原因 2：路由配置錯誤
**症狀**：請求無法路由到正確的函數
**解決方案**：
- 檢查 `vercel.json` 配置
- 確保路由規則正確
- 使用明確的路由規則

#### 原因 3：函數名稱不匹配
**症狀**：檔案名稱與配置不匹配
**解決方案**：
- 確保 `vercel.json` 中的 `src` 指向正確的檔案
- 檢查檔案名稱是否正確

#### 原因 4：Python 版本問題
**症狀**：函數無法在指定 Python 版本下運行
**解決方案**：
- 檢查 `runtime.txt` 中的 Python 版本
- 確保版本與依賴套件相容

### 步驟 5：使用簡化版本測試

如果問題持續，可以暫時使用簡化版本：

1. **替換主檔案**：
   ```bash
   mv app.py app_backup.py
   mv test_app.py app.py
   mv vercel_test.json vercel.json
   ```

2. **重新部署**：
   ```bash
   git add .
   git commit -m "使用簡化版本測試"
   git push origin main
   ```

3. **測試端點**：
   - 訪問：`https://your-project.vercel.app/`
   - 應該看到：`{"message": "Hello from Vercel!", "status": "ok"}`

### 步驟 6：檢查檔案結構

確保您的專案結構如下：

```
ai-line-bot/
├── app.py              # 主應用程式檔案
├── vercel.json         # Vercel 配置
├── requirements.txt    # Python 依賴
├── runtime.txt         # Python 版本
└── .gitignore         # Git 忽略檔案
```

### 步驟 7：重新部署

如果修改了配置，需要重新部署：

1. **自動部署**：推送到 GitHub 主分支
2. **手動部署**：在 Vercel Dashboard 中點擊 "Redeploy"

## 🔧 進階故障排除

### 檢查 Vercel 日誌

1. 前往 Vercel Dashboard
2. 選擇您的專案
3. 點擊 **Functions** 標籤
4. 查看 `app.py` 的構建和執行日誌

### 檢查函數狀態

在 Vercel Dashboard 中：
- 確認函數已成功構建
- 檢查函數是否在線
- 查看函數的錯誤日誌

### 測試本地部署

在本地測試應用程式：

```bash
# 安裝依賴
pip install -r requirements.txt

# 運行應用程式
python app.py

# 測試端點
curl http://localhost:8080/
```

## 📋 快速檢查清單

- [ ] Vercel 部署狀態為 "Ready"
- [ ] 函數已正確構建
- [ ] 路由配置正確
- [ ] 檔案名稱匹配
- [ ] Python 版本正確
- [ ] 依賴套件已安裝

## 📞 需要幫助？

如果按照以上步驟仍然無法解決問題，請提供：

1. **您的 Vercel 專案 URL**
2. **Vercel Dashboard 中的部署狀態**
3. **函數構建日誌**
4. **具體的錯誤訊息**

這樣我就能更精確地幫您診斷問題！

---

**💡 提示**：404 錯誤通常是由部署失敗或路由配置問題造成的。請優先檢查 Vercel Dashboard 中的部署狀態和函數構建日誌。 