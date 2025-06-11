// pages/api/trip-detail.js - 修復版本
import { query } from '../../lib/db';

export default async function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ message: 'Method not allowed' });
    }

    try {
        const { id } = req.query;

        console.log('trip-detail API called with id:', id);

        if (!id) {
            return res.status(400).json({ message: '缺少行程 ID' });
        }

        // 獲取行程資訊
        const tripSql = `
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
        t.updated_at,
        u.username as creator_name,
        0 as view_count
      FROM trip t 
      JOIN users u ON t.user_id = u.user_id 
      WHERE t.trip_id = ?
    `;

        console.log('Executing trip query with ID:', id);
        const tripResult = await query(tripSql, [parseInt(id)]);

        if (tripResult.length === 0) {
            return res.status(404).json({ message: '找不到該行程' });
        }

        console.log('Trip found:', tripResult[0].title);

        // 獲取行程細節
        const detailsSql = `
      SELECT 
        detail_id,
        trip_id,
        location,
        date,
        start_time,
        end_time
      FROM trip_detail 
      WHERE trip_id = ? 
      ORDER BY date ASC, start_time ASC
    `;

        console.log('Fetching trip details...');
        const details = await query(detailsSql, [parseInt(id)]);
        console.log('Details found:', details.length);

        // 獲取參與者
        const participantsSql = `
      SELECT 
        tp.participant_id,
        tp.trip_id,
        tp.user_id,
        tp.status,
        tp.created_at,
        u.username 
      FROM trip_participants tp 
      JOIN users u ON tp.user_id = u.user_id 
      WHERE tp.trip_id = ?
    `;

        console.log('Fetching participants...');
        const participants = await query(participantsSql, [parseInt(id)]);
        console.log('Participants found:', participants.length);

        res.status(200).json({
            trip: tripResult[0],
            details: details,
            participants: participants
        });

    } catch (error) {
        console.error('trip-detail API Error:', error);
        res.status(500).json({
            message: '伺服器錯誤',
            error: error.message
        });
    }
}