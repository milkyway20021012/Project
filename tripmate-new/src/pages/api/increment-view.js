// pages/api/increment-view.js - 瀏覽次數增加 API（模擬功能）
export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ message: 'Method not allowed' });
    }

    try {
        const { tripId } = req.body;

        if (!tripId) {
            return res.status(400).json({ message: '缺少行程 ID' });
        }

        // 由於你的資料庫沒有 view_count 欄位，我們模擬這個功能
        // 在實際應用中，你可能需要添加 view_count 欄位到 trip 表格
        console.log(`模擬增加行程 ${tripId} 的瀏覽次數`);

        res.status(200).json({
            message: '瀏覽次數已更新',
            view_count: Math.floor(Math.random() * 100) + 1 // 模擬瀏覽次數
        });

    } catch (error) {
        console.error('API Error:', error);
        res.status(500).json({ message: '伺服器錯誤', error: error.message });
    }
}