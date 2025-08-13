// 集合管理網站 (TourClock) 需要添加的 API 端點
// 檔案位置：pages/api/line-bot/meetings.js

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
    
    const response = await axios.post(`${AUTH_SERVICE_URL}/api/auth/verify-token`, {
      line_user_id,
      unified_token
    });
    
    if (response.data.valid) {
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

// API 端點：創建集合
app.post('/api/line-bot/meetings', verifyUnifiedToken, async (req, res) => {
  try {
    const { line_user_id, meeting_data } = req.body;
    
    console.log('⏰ Line Bot 創建集合請求:', {
      line_user_id,
      meeting_data
    });
    
    // 獲取或創建網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 解析時間資訊
    const { time_info } = meeting_data;
    let meetingDate = null;
    let meetingTime = null;
    
    if (time_info) {
      meetingDate = time_info.date || new Date().toISOString().split('T')[0];
      meetingTime = time_info.time || '09:00';
    }
    
    // 創建集合
    const meeting = await Meeting.create({
      title: meeting_data.title,
      location: meeting_data.location,
      description: meeting_data.description,
      meeting_date: meetingDate,
      meeting_time: meetingTime,
      organizer_id: websiteUser.id,
      created_via: 'line_bot',
      status: 'active',
      created_at: new Date()
    });
    
    console.log('✅ 集合創建成功:', meeting.id);
    
    // 返回結果
    res.json({
      success: true,
      meeting_id: meeting.id,
      message: '集合創建成功',
      url: `/meeting/${meeting.id}`,
      data: {
        id: meeting.id,
        title: meeting.title,
        location: meeting.location,
        meeting_date: meeting.meeting_date,
        meeting_time: meeting.meeting_time,
        created_at: meeting.created_at
      }
    });
    
  } catch (error) {
    console.error('❌ 創建集合錯誤:', error);
    res.status(500).json({
      success: false,
      error: '創建集合失敗',
      details: error.message
    });
  }
});

// API 端點：獲取用戶集合列表
app.get('/api/line-bot/meetings', verifyUnifiedToken, async (req, res) => {
  try {
    const { line_user_id } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查詢用戶的集合
    const meetings = await Meeting.find({ 
      $or: [
        { organizer_id: websiteUser.id },
        { participants: websiteUser.id }
      ]
    })
    .sort({ meeting_date: 1, meeting_time: 1 })
    .limit(10);
    
    res.json({
      success: true,
      meetings: meetings.map(meeting => ({
        id: meeting.id,
        title: meeting.title,
        location: meeting.location,
        meeting_date: meeting.meeting_date,
        meeting_time: meeting.meeting_time,
        status: meeting.status,
        created_at: meeting.created_at,
        url: `/meeting/${meeting.id}`
      }))
    });
    
  } catch (error) {
    console.error('❌ 獲取集合錯誤:', error);
    res.status(500).json({
      success: false,
      error: '獲取集合失敗'
    });
  }
});

// API 端點：更新集合
app.put('/api/line-bot/meetings/:meeting_id', verifyUnifiedToken, async (req, res) => {
  try {
    const { meeting_id } = req.params;
    const { line_user_id, meeting_data } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查找並更新集合
    const meeting = await Meeting.findOneAndUpdate(
      { id: meeting_id, organizer_id: websiteUser.id },
      {
        ...meeting_data,
        updated_at: new Date()
      },
      { new: true }
    );
    
    if (!meeting) {
      return res.status(404).json({
        success: false,
        error: '集合不存在或無權限'
      });
    }
    
    res.json({
      success: true,
      meeting_id: meeting.id,
      message: '集合更新成功',
      data: meeting
    });
    
  } catch (error) {
    console.error('❌ 更新集合錯誤:', error);
    res.status(500).json({
      success: false,
      error: '更新集合失敗'
    });
  }
});

// API 端點：加入集合
app.post('/api/line-bot/meetings/:meeting_id/join', verifyUnifiedToken, async (req, res) => {
  try {
    const { meeting_id } = req.params;
    const { line_user_id } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查找集合
    const meeting = await Meeting.findById(meeting_id);
    
    if (!meeting) {
      return res.status(404).json({
        success: false,
        error: '集合不存在'
      });
    }
    
    // 檢查是否已經參加
    if (meeting.participants.includes(websiteUser.id)) {
      return res.json({
        success: true,
        message: '您已經參加此集合'
      });
    }
    
    // 添加參與者
    meeting.participants.push(websiteUser.id);
    await meeting.save();
    
    res.json({
      success: true,
      message: '成功加入集合',
      meeting_id: meeting.id
    });
    
  } catch (error) {
    console.error('❌ 加入集合錯誤:', error);
    res.status(500).json({
      success: false,
      error: '加入集合失敗'
    });
  }
});

module.exports = app;
