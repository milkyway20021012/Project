// pages/api/trips-minimal.js - 極簡版本
import { query } from '../../lib/db';

export default async function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ message: 'Method not allowed' });
    }

    try {
        console.log('極簡版 trips API 開始');

        // 最簡單的查詢 - 無參數
        const sql = `
      SELECT 
        t.trip_id,
        t.title,
        t.description,
        t.start_date,
        t.end_date,
        t.area,
        t.tags,
        t.budget,
        u.username as creator_name,
        0 as view_count,
        0 as total_participants
      FROM trip t 
      JOIN users u ON t.user_id = u.user_id 
      ORDER BY t.created_at DESC
      LIMIT 10
    `;

        console.log('執行極簡查詢...');
        const trips = await query(sql, []); // 空參數數組

        console.log('查詢成功，返回', trips.length, '筆記錄');

        res.status(200).json({
            data: trips,
            pagination: {
                total: trips.length,
                total_pages: 1,
                current_page: 1,
                limit: 10
            },
            message: '極簡版查詢成功'
        });

    } catch (error) {
        console.error('極簡版查詢失敗:', error);
        res.status(500).json({
            message: '極簡版查詢失敗',
            error: error.message,
            code: error.code
        });
    }
}