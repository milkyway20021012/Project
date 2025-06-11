// pages/api/trip-rankings.js - 修復版本
import { query } from '../../lib/db';

export default async function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ message: 'Method not allowed' });
    }

    try {
        const { type = 'view' } = req.query;

        console.log('trip-rankings API called with type:', type);

        let sql = '';

        switch (type) {
            case 'view':
                // 最多瀏覽（按參與者數量排序）
                sql = `
          SELECT 
            t.trip_id,
            t.user_id,
            t.title,
            t.description,
            t.start_date,
            t.end_date,
            t.area,
            t.tags,
            t.budget,
            t.created_at,
            u.username as creator_name,
            (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id) as total_participants,
            (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id) * 10 as view_count
          FROM trip t 
          JOIN users u ON t.user_id = u.user_id 
          ORDER BY total_participants DESC, t.created_at DESC
          LIMIT 20
        `;
                break;

            case 'area':
                // 熱門地區（每個地區選一個最熱門的）
                sql = `
          SELECT 
            t.trip_id,
            t.user_id,
            t.title,
            t.description,
            t.start_date,
            t.end_date,
            t.area,
            t.tags,
            t.budget,
            t.created_at,
            u.username as creator_name,
            (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id) as total_participants,
            (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id) * 10 as view_count
          FROM trip t 
          JOIN users u ON t.user_id = u.user_id 
          ORDER BY total_participants DESC, t.created_at DESC
          LIMIT 20
        `;
                break;

            case 'date':
                // 即將出發
                sql = `
          SELECT 
            t.trip_id,
            t.user_id,
            t.title,
            t.description,
            t.start_date,
            t.end_date,
            t.area,
            t.tags,
            t.budget,
            t.created_at,
            u.username as creator_name,
            (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id) as total_participants,
            (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id) * 10 as view_count
          FROM trip t 
          JOIN users u ON t.user_id = u.user_id 
          WHERE t.start_date >= CURDATE()
          ORDER BY t.start_date ASC, total_participants DESC
          LIMIT 20
        `;
                break;

            default:
                return res.status(400).json({ message: '無效的排行榜類型' });
        }

        console.log('Executing ranking query...');
        const trips = await query(sql);
        console.log('Ranking results:', trips.length);

        res.status(200).json(trips);

    } catch (error) {
        console.error('trip-rankings API Error:', error);
        res.status(500).json({
            message: '伺服器錯誤',
            error: error.message
        });
    }
}