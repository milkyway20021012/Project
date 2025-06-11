// pages/api/simple-test.js - 簡單測試 API
import { testConnection, query } from '../../lib/db';

export default async function handler(req, res) {
    try {
        // 測試基本連接
        const connectionTest = await testConnection();

        if (!connectionTest) {
            return res.status(500).json({
                success: false,
                message: '資料庫連接失敗'
            });
        }

        // 查詢現有的表格
        const tables = await query('SHOW TABLES');

        // 測試查詢 users 表（如果存在）
        let usersData = [];
        try {
            usersData = await query('SELECT COUNT(*) as user_count FROM users LIMIT 1');
        } catch (error) {
            console.log('users 表查詢失敗:', error.message);
        }

        // 測試查詢 trip 表（如果存在）
        let tripsData = [];
        try {
            tripsData = await query('SELECT COUNT(*) as trip_count FROM trip LIMIT 1');
        } catch (error) {
            console.log('trip 表查詢失敗:', error.message);
        }

        res.status(200).json({
            success: true,
            message: '資料庫連接成功！',
            data: {
                database: 'tourhub',
                tables: tables.map(table => Object.values(table)[0]),
                tableCount: tables.length,
                userCount: usersData[0]?.user_count || 0,
                tripCount: tripsData[0]?.trip_count || 0
            },
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('測試 API 錯誤:', error);

        res.status(500).json({
            success: false,
            message: '測試失敗',
            error: error.message,
            code: error.code
        });
    }
}