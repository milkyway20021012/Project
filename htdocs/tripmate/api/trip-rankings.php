<?php
// C:\xampp\htdocs\tripmate\api\trip-rankings.php

// 設置允許跨域請求，這對於 React 前端非常重要
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *'); // 允許所有來源的請求，生產環境應限制為您的前端域名
header('Access-Control-Allow-Methods: GET');
header('Access-Control-Allow-Headers: Content-Type');

// 資料庫連接參數
$host = 'localhost';
$dbname = 'tripmate';
$username = 'root';
$password = '';

// 獲取排名類型（預設為瀏覽量）
$rankingType = isset($_GET['type']) ? $_GET['type'] : 'view';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // 根據不同排名類型選擇不同的查詢
    switch($rankingType) {
        case 'view':
            // 最多瀏覽量的行程
            $sql = "
                SELECT t.*, 
                      (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id AND tp.status = 'accepted') as total_participants,
                      u.username as creator_name
                FROM trip t
                JOIN users u ON t.user_id = u.user_id
                ORDER BY t.view_count DESC, t.created_at DESC
                LIMIT 10
            ";
            break;
            
        case 'area':
            // 熱門地區
            $sql = "
                SELECT t.*, 
                      (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id AND tp.status = 'accepted') as total_participants,
                      u.username as creator_name,
                      (SELECT COUNT(*) FROM trip t2 WHERE t2.area = t.area) as area_count
                FROM trip t
                JOIN users u ON t.user_id = u.user_id
                GROUP BY t.area
                ORDER BY area_count DESC, t.view_count DESC
                LIMIT 10
            ";
            break;
            
        case 'date':
            // 即將到來的行程
            $sql = "
                SELECT t.*, 
                      (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id AND tp.status = 'accepted') as total_participants,
                      u.username as creator_name
                FROM trip t
                JOIN users u ON t.user_id = u.user_id
                WHERE t.start_date >= CURDATE()
                ORDER BY t.start_date ASC
                LIMIT 10
            ";
            break;
            
        default:
            // 預設為最多瀏覽
            $sql = "
                SELECT t.*, 
                      (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id AND tp.status = 'accepted') as total_participants,
                      u.username as creator_name
                FROM trip t
                JOIN users u ON t.user_id = u.user_id
                ORDER BY t.view_count DESC, t.created_at DESC
                LIMIT 10
            ";
    }
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $trips = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($trips);
    
} catch(PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
}
?>