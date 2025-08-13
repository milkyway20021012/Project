// 行程管理網站需要添加的 API 端點
// 檔案位置：routes/line-bot.js 或 pages/api/line-bot/trips.js

const axios = require('axios');

// 統一認證服務 URL
const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'https://your-auth-service.vercel.app';

// 驗證統一 Token 的中間件
async function verifyUnifiedToken(req, res, next) {
  try {
    const { line_user_id, unified_token } = req.body;
    
    if (!line_user_id || !unified_token) {
      return res.status(400).json({
        success: false,
        error: '缺少認證資訊'
      });
    }
    
    // 調用統一認證服務驗證 Token
    const response = await axios.post(`${AUTH_SERVICE_URL}/api/auth/verify-token`, {
      line_user_id,
      unified_token
    });
    
    if (response.data.valid) {
      // Token 有效，將用戶資訊附加到請求
      req.lineUser = response.data;
      next();
    } else {
      return res.status(401).json({
        success: false,
        error: '認證失敗'
      });
    }
    
  } catch (error) {
    console.error('Token 驗證錯誤:', error);
    return res.status(500).json({
      success: false,
      error: '認證服務錯誤'
    });
  }
}

// 獲取或創建網站用戶
async function getOrCreateWebsiteUser(line_user_id) {
  // 根據你的資料庫結構調整
  let user = await User.findOne({ line_user_id });
  
  if (!user) {
    user = await User.create({
      line_user_id,
      created_via: 'line_bot',
      created_at: new Date()
    });
  }
  
  return user;
}

// API 端點：創建行程
app.post('/api/line-bot/trips', verifyUnifiedToken, async (req, res) => {
  try {
    const { line_user_id, trip_data } = req.body;
    
    console.log('📝 Line Bot 創建行程請求:', {
      line_user_id,
      trip_data
    });
    
    // 獲取或創建網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 創建行程
    const trip = await Trip.create({
      title: trip_data.title,
      location: trip_data.location,
      days: trip_data.days,
      description: trip_data.description,
      user_id: websiteUser.id,
      created_via: 'line_bot',
      created_at: new Date()
    });
    
    console.log('✅ 行程創建成功:', trip.id);
    
    // 返回結果
    res.json({
      success: true,
      trip_id: trip.id,
      message: '行程創建成功',
      url: `/trip/${trip.id}`,
      data: {
        id: trip.id,
        title: trip.title,
        location: trip.location,
        days: trip.days,
        created_at: trip.created_at
      }
    });
    
  } catch (error) {
    console.error('❌ 創建行程錯誤:', error);
    res.status(500).json({
      success: false,
      error: '創建行程失敗',
      details: error.message
    });
  }
});

// API 端點：獲取用戶行程列表
app.get('/api/line-bot/trips', verifyUnifiedToken, async (req, res) => {
  try {
    const { line_user_id } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查詢用戶的行程
    const trips = await Trip.find({ user_id: websiteUser.id })
      .sort({ created_at: -1 })
      .limit(10);
    
    res.json({
      success: true,
      trips: trips.map(trip => ({
        id: trip.id,
        title: trip.title,
        location: trip.location,
        days: trip.days,
        created_at: trip.created_at,
        url: `/trip/${trip.id}`
      }))
    });
    
  } catch (error) {
    console.error('❌ 獲取行程錯誤:', error);
    res.status(500).json({
      success: false,
      error: '獲取行程失敗'
    });
  }
});

// API 端點：更新行程
app.put('/api/line-bot/trips/:trip_id', verifyUnifiedToken, async (req, res) => {
  try {
    const { trip_id } = req.params;
    const { line_user_id, trip_data } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查找並更新行程
    const trip = await Trip.findOneAndUpdate(
      { id: trip_id, user_id: websiteUser.id },
      {
        ...trip_data,
        updated_at: new Date()
      },
      { new: true }
    );
    
    if (!trip) {
      return res.status(404).json({
        success: false,
        error: '行程不存在或無權限'
      });
    }
    
    res.json({
      success: true,
      trip_id: trip.id,
      message: '行程更新成功',
      data: trip
    });
    
  } catch (error) {
    console.error('❌ 更新行程錯誤:', error);
    res.status(500).json({
      success: false,
      error: '更新行程失敗'
    });
  }
});

// API 端點：刪除行程
app.delete('/api/line-bot/trips/:trip_id', verifyUnifiedToken, async (req, res) => {
  try {
    const { trip_id } = req.params;
    const { line_user_id } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查找並刪除行程
    const trip = await Trip.findOneAndDelete({
      id: trip_id,
      user_id: websiteUser.id
    });
    
    if (!trip) {
      return res.status(404).json({
        success: false,
        error: '行程不存在或無權限'
      });
    }
    
    res.json({
      success: true,
      message: '行程刪除成功'
    });
    
  } catch (error) {
    console.error('❌ 刪除行程錯誤:', error);
    res.status(500).json({
      success: false,
      error: '刪除行程失敗'
    });
  }
});

// 錯誤處理中間件
app.use('/api/line-bot/*', (error, req, res, next) => {
  console.error('Line Bot API 錯誤:', error);
  res.status(500).json({
    success: false,
    error: '服務器內部錯誤'
  });
});

module.exports = app;
