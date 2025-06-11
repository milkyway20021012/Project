// pages/api/explore-tables.js - 探索資料庫表格結構
import { query } from '../../lib/db';

export default async function handler(req, res) {
    try {
        // 獲取所有表格
        const tables = await query('SHOW TABLES');
        const tableNames = tables.map(table => Object.values(table)[0]);

        const tableStructures = {};

        // 查看每個表格的結構
        for (const tableName of tableNames) {
            try {
                const structure = await query(`DESCRIBE ${tableName}`);
                const sampleData = await query(`SELECT * FROM ${tableName} LIMIT 3`);

                tableStructures[tableName] = {
                    columns: structure,
                    sampleData: sampleData,
                    rowCount: sampleData.length
                };
            } catch (error) {
                tableStructures[tableName] = {
                    error: error.message
                };
            }
        }

        res.status(200).json({
            success: true,
            message: '表格結構探索完成',
            database: 'tourhub',
            tables: tableNames,
            structures: tableStructures,
            suggestions: {
                tripTable: tableNames.includes('trip') ? 'trip' :
                    tableNames.includes('trips') ? 'trips' :
                        tableNames.includes('line_trips') ? 'line_trips' : '未找到',
                userTable: tableNames.includes('users') ? 'users' :
                    tableNames.includes('line_users') ? 'line_users' : '未找到'
            }
        });

    } catch (error) {
        console.error('探索表格錯誤:', error);

        res.status(500).json({
            success: false,
            message: '探索表格失敗',
            error: error.message
        });
    }
}