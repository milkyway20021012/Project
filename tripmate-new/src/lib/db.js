// lib/db.js - 最終版 MySQL 資料庫連接
import mysql from 'mysql2/promise';

// 建立連接池
const pool = mysql.createPool({
    host: process.env.MYSQL_HOST,
    user: process.env.MYSQL_USER,
    password: process.env.MYSQL_PASSWORD,
    database: process.env.MYSQL_DB,
    port: parseInt(process.env.MYSQL_PORT) || 3306,
    ssl: {
        rejectUnauthorized: false
    },
    connectionLimit: 10,
    queueLimit: 0,
    acquireTimeout: 60000,
    timeout: 60000,
    reconnect: true,
    charset: 'utf8mb4'
});

// 查詢函數
export async function query(sql, params = []) {
    try {
        console.log('執行查詢:', sql);
        const [results] = await pool.execute(sql, params);
        return results;
    } catch (error) {
        console.error('資料庫查詢錯誤:', error);
        throw error;
    }
}

// 測試連接 - 使用簡單的查詢
export async function testConnection() {
    try {
        // 使用最簡單的查詢來測試
        const result = await query('SELECT 1 as test');
        console.log('資料庫連接成功');
        return true;
    } catch (error) {
        console.error('資料庫連接失敗:', error);
        return false;
    }
}