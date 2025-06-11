// pages/api/get-filters.js - 修復版本
import { query } from '../../lib/db';

export default async function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ message: 'Method not allowed' });
    }

    try {
        console.log('get-filters API called');

        // 獲取所有地區 - 簡化查詢
        const areasResult = await query(`
      SELECT DISTINCT area 
      FROM trip 
      WHERE area IS NOT NULL AND area != '' 
      ORDER BY area
    `);

        // 獲取所有標籤 - 簡化版本，不使用複雜的字串分割
        const tagsResult = await query(`
      SELECT DISTINCT tags
      FROM trip 
      WHERE tags IS NOT NULL AND tags != ''
    `);

        const areas = areasResult.map(row => row.area);

        // 處理標籤 - 在 JavaScript 中分割而不是在 SQL 中
        const allTagsSet = new Set();
        tagsResult.forEach(row => {
            if (row.tags) {
                const tagArray = row.tags.split(',');
                tagArray.forEach(tag => {
                    const trimmedTag = tag.trim();
                    if (trimmedTag) {
                        allTagsSet.add(trimmedTag);
                    }
                });
            }
        });

        const tags = Array.from(allTagsSet).sort();

        console.log('Areas found:', areas.length);
        console.log('Tags found:', tags.length);

        res.status(200).json({
            areas,
            tags
        });

    } catch (error) {
        console.error('get-filters API Error:', error);
        res.status(500).json({
            message: '伺服器錯誤',
            error: error.message
        });
    }
}