// 分帳系統網站需要添加的 API 端點
// 檔案位置：pages/api/line-bot/bills.js

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

// API 端點：創建分帳
app.post('/api/line-bot/bills', verifyUnifiedToken, async (req, res) => {
  try {
    const { line_user_id, bill_data } = req.body;
    
    console.log('💰 Line Bot 創建分帳請求:', {
      line_user_id,
      bill_data
    });
    
    // 獲取或創建網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 創建分帳
    const bill = await Bill.create({
      title: bill_data.title,
      description: bill_data.description,
      currency: bill_data.currency || 'TWD',
      creator_id: websiteUser.id,
      participants: [websiteUser.id], // 創建者自動成為參與者
      total_amount: 0,
      status: 'active',
      created_via: 'line_bot',
      created_at: new Date()
    });
    
    console.log('✅ 分帳創建成功:', bill.id);
    
    // 返回結果
    res.json({
      success: true,
      bill_id: bill.id,
      message: '分帳創建成功',
      url: `/bill/${bill.id}`,
      data: {
        id: bill.id,
        title: bill.title,
        currency: bill.currency,
        total_amount: bill.total_amount,
        participants_count: bill.participants.length,
        created_at: bill.created_at
      }
    });
    
  } catch (error) {
    console.error('❌ 創建分帳錯誤:', error);
    res.status(500).json({
      success: false,
      error: '創建分帳失敗',
      details: error.message
    });
  }
});

// API 端點：獲取用戶分帳列表
app.get('/api/line-bot/bills', verifyUnifiedToken, async (req, res) => {
  try {
    const { line_user_id } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查詢用戶參與的分帳
    const bills = await Bill.find({ 
      participants: websiteUser.id 
    })
    .sort({ created_at: -1 })
    .limit(10);
    
    res.json({
      success: true,
      bills: bills.map(bill => ({
        id: bill.id,
        title: bill.title,
        currency: bill.currency,
        total_amount: bill.total_amount,
        participants_count: bill.participants.length,
        status: bill.status,
        created_at: bill.created_at,
        url: `/bill/${bill.id}`
      }))
    });
    
  } catch (error) {
    console.error('❌ 獲取分帳錯誤:', error);
    res.status(500).json({
      success: false,
      error: '獲取分帳失敗'
    });
  }
});

// API 端點：添加費用
app.post('/api/line-bot/bills/:bill_id/expenses', verifyUnifiedToken, async (req, res) => {
  try {
    const { bill_id } = req.params;
    const { line_user_id, expense_data } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查找分帳
    const bill = await Bill.findById(bill_id);
    
    if (!bill) {
      return res.status(404).json({
        success: false,
        error: '分帳不存在'
      });
    }
    
    // 檢查用戶是否為參與者
    if (!bill.participants.includes(websiteUser.id)) {
      return res.status(403).json({
        success: false,
        error: '您不是此分帳的參與者'
      });
    }
    
    // 創建費用記錄
    const expense = await Expense.create({
      bill_id: bill.id,
      payer_id: websiteUser.id,
      amount: expense_data.amount,
      description: expense_data.description,
      category: expense_data.category || 'other',
      date: expense_data.date || new Date(),
      created_at: new Date()
    });
    
    // 更新分帳總金額
    bill.total_amount += expense_data.amount;
    await bill.save();
    
    res.json({
      success: true,
      expense_id: expense.id,
      message: '費用添加成功',
      data: {
        id: expense.id,
        amount: expense.amount,
        description: expense.description,
        new_total: bill.total_amount
      }
    });
    
  } catch (error) {
    console.error('❌ 添加費用錯誤:', error);
    res.status(500).json({
      success: false,
      error: '添加費用失敗'
    });
  }
});

// API 端點：加入分帳
app.post('/api/line-bot/bills/:bill_id/join', verifyUnifiedToken, async (req, res) => {
  try {
    const { bill_id } = req.params;
    const { line_user_id } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查找分帳
    const bill = await Bill.findById(bill_id);
    
    if (!bill) {
      return res.status(404).json({
        success: false,
        error: '分帳不存在'
      });
    }
    
    // 檢查是否已經參加
    if (bill.participants.includes(websiteUser.id)) {
      return res.json({
        success: true,
        message: '您已經參加此分帳'
      });
    }
    
    // 添加參與者
    bill.participants.push(websiteUser.id);
    await bill.save();
    
    res.json({
      success: true,
      message: '成功加入分帳',
      bill_id: bill.id
    });
    
  } catch (error) {
    console.error('❌ 加入分帳錯誤:', error);
    res.status(500).json({
      success: false,
      error: '加入分帳失敗'
    });
  }
});

// API 端點：計算分帳結果
app.get('/api/line-bot/bills/:bill_id/calculate', verifyUnifiedToken, async (req, res) => {
  try {
    const { bill_id } = req.params;
    const { line_user_id } = req.body;
    
    // 獲取網站用戶
    const websiteUser = await getOrCreateWebsiteUser(line_user_id);
    
    // 查找分帳和相關費用
    const bill = await Bill.findById(bill_id);
    const expenses = await Expense.find({ bill_id: bill.id });
    
    if (!bill) {
      return res.status(404).json({
        success: false,
        error: '分帳不存在'
      });
    }
    
    // 計算每人應付金額
    const totalAmount = bill.total_amount;
    const participantCount = bill.participants.length;
    const perPersonAmount = totalAmount / participantCount;
    
    // 計算每個人的支付和應付
    const calculations = {};
    
    // 初始化每個參與者
    bill.participants.forEach(participantId => {
      calculations[participantId] = {
        paid: 0,
        shouldPay: perPersonAmount,
        balance: 0
      };
    });
    
    // 計算每個人實際支付的金額
    expenses.forEach(expense => {
      if (calculations[expense.payer_id]) {
        calculations[expense.payer_id].paid += expense.amount;
      }
    });
    
    // 計算餘額
    Object.keys(calculations).forEach(participantId => {
      const calc = calculations[participantId];
      calc.balance = calc.paid - calc.shouldPay;
    });
    
    res.json({
      success: true,
      bill_id: bill.id,
      total_amount: totalAmount,
      per_person_amount: perPersonAmount,
      calculations: calculations
    });
    
  } catch (error) {
    console.error('❌ 計算分帳錯誤:', error);
    res.status(500).json({
      success: false,
      error: '計算分帳失敗'
    });
  }
});

module.exports = app;
