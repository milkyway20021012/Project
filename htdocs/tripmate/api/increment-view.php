<?php
// C:\xampp\htdocs\tripmate\api\increment-view.php

// 設置允許跨域請求
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// 處理 OPTIONS 請求（瀏覽器的預檢請求）
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// 只允許 POST 請求
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// 資料庫連接參數
$host = 'localhost';
$dbname = 'tripmate';
$username = 'root';
$password = '';

// 獲取 POST 數據
$data = json_decode(file_get_contents('php://input'), true);
$tripId = isset($data['tripId']) ? intval($data['tripId']) : 0;

if ($tripId <= 0) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid trip ID']);
    exit;
}

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // 增加瀏覽次數
    $sql = "UPDATE trip SET view_count = view_count + 1 WHERE trip_id = :tripId";
    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(':tripId', $tripId, PDO::PARAM_INT);
    $stmt->execute();
    
    // 返回成功響應
    echo json_encode(['success' => true, 'message' => 'View count incremented']);
    
} catch(PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
}
?>