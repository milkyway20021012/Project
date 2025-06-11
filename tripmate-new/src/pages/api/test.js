// pages/api/test.js - 基本測試 API
import { testConnection, query } from '../../lib/db';

export default async function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ message: 'Method not allowed' });
    }

    try {
        // 測試環境變數
        const envCheck = {
            MYSQL_HOST: process.env.MYSQL_HOST || '❌ 未設定',
            MYSQL_USER: process.env.MYSQL_USER || '❌ 未設定',
            MYSQL_PASSWORD: process.env.MYSQL_PASSWORD ? '✅ 已設定' : '❌ 未設定',
            MYSQL_DB: process.env.MYSQL_DB || '❌ 未設定',
        };

        // 測試資料庫連接
        const connectionTest = await testConnection();

        if (!connectionTest) {
            return res.status(500).json({
                success: false,
                message: '資料庫連接失敗',
                envCheck,
                timestamp: new Date().toISOString()
            });
        }

        // 查詢資料庫資訊
        const dbInfo = await query('SELECT NOW() as current_time, DATABASE() as db_name, VERSION() as version');
        const tables = await query('SHOW TABLES');

        res.status(200).json({
            success: true,
            message: '所有測試通過！',
            envCheck,
            database: {
                name: dbInfo[0].db_name,
                version: dbInfo[0].version,
                currentTime: dbInfo[0].current_time,
                tables: tables.map(table => Object.values(table)[0]),
                tableCount: tables.length
            },
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('測試 API 錯誤:', error);

        res.status(500).json({
            success: false,
            message: '測試失敗',
            error: error.message,
            code: error.code,
            timestamp: new Date().toISOString()
        });
    }
}