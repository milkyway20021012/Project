// pages/api/trips-paged-v2.js - 基於可工作查詢的完整版本
import { query } from '../../lib/db';

export default async function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ message: 'Method not allowed' });
    }

    try {
        console.log('trips-paged-v2 API called');
        console.log('Query params:', req.query);

        const {
            page = 1,
            limit = 10,
            sort = 'created_at',
            order = 'DESC',
            area = '',
            tag = '',
            startDate = '',
            endDate = '',
            search = ''
        } = req.query;

        // 使用與 trips-minimal 相同的基本查詢結構
        let baseSql = `
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
    `;

        // 只在有篩選條件時才添加 WHERE
        let whereConditions = [];
        let queryParams = [];

        // 處理篩選條件
        if (area && area.trim()) {
            whereConditions.push("t.area = '" + area.trim().replace(/'/g, "''") + "'");
        }

        if (search && search.trim()) {
            const searchTerm = search.trim().replace(/'/g, "''");
            whereConditions.push("(t.title LIKE '%" + searchTerm + "%' OR t.description LIKE '%" + searchTerm + "%')");
        }

        if (tag && tag.trim()) {
            const tagTerm = tag.trim().replace(/'/g, "''");
            whereConditions.push("t.tags LIKE '%" + tagTerm + "%'");
        }

        if (startDate && startDate.trim()) {
            whereConditions.push("t.start_date >= '" + startDate.trim() + "'");
        }

        if (endDate && endDate.trim()) {
            whereConditions.push("t.end_date <= '" + endDate.trim() + "'");
        }

        // 組建完整的查詢
        let whereSql = '';
        if (whereConditions.length > 0) {
            whereSql = ' WHERE ' + whereConditions.join(' AND ');
        }

        // 計算總數（先不用參數綁定）
        const countSql = `
      SELECT COUNT(*) as total 
      FROM trip t 
      JOIN users u ON t.user_id = u.user_id
      ${whereSql}
    `;

        console.log('Count SQL:', countSql);
        const countResult = await query(countSql, []);
        const total = countResult[0].total;

        // 處理分頁
        const pageNum = Math.max(1, parseInt(page) || 1);
        const limitNum = Math.min(100, Math.max(1, parseInt(limit) || 10));
        const offset = (pageNum - 1) * limitNum;
        const totalPages = Math.ceil(total / limitNum);

        // 處理排序
        const allowedSortFields = ['title', 'start_date', 'end_date', 'area', 'created_at'];
        const sortField = allowedSortFields.includes(sort) ? sort : 'created_at';
        const sortOrder = (order && order.toUpperCase() === 'ASC') ? 'ASC' : 'DESC';

        // 組建數據查詢
        const dataSql = `
      ${baseSql}
      ${whereSql}
      ORDER BY t.${sortField} ${sortOrder}
      LIMIT ${limitNum} OFFSET ${offset}
    `;

        console.log('Data SQL:', dataSql);
        const trips = await query(dataSql, []);

        console.log('Query successful, rows:', trips.length);

        res.status(200).json({
            data: trips,
            pagination: {
                total: parseInt(total),
                total_pages: totalPages,
                current_page: pageNum,
                limit: limitNum
            }
        });

    } catch (error) {
        console.error('trips-paged-v2 error:', error);
        res.status(500).json({
            message: '伺服器錯誤',
            error: error.message,
            code: error.code
        });
    }
}