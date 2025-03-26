<?php
// C:\xampp\htdocs\tripmate\api\trip-detail.php

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');
header('Access-Control-Allow-Headers: Content-Type');

// 資料庫連接參數
$host = 'localhost';
$dbname = 'tripmate';
$username = 'root';
$password = '';

// 獲取行程ID
$tripId = isset($_GET['id']) ? intval($_GET['id']) : 0;

if ($tripId <= 0) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid trip ID']);
    exit;
}

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // 獲取行程基本信息
    $tripQuery = "
        SELECT t.*,
               u.username as creator_name,
               (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id AND tp.status = 'accepted') as total_participants
        FROM trip t
        JOIN users u ON t.user_id = u.user_id
        WHERE t.trip_id = :tripId
    ";
    
    $tripStmt = $pdo->prepare($tripQuery);
    $tripStmt->bindParam(':tripId', $tripId, PDO::PARAM_INT);
    $tripStmt->execute();
    $trip = $tripStmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$trip) {
        http_response_code(404);
        echo json_encode(['error' => 'Trip not found']);
        exit;
    }
    
    // 獲取行程詳細信息
    $detailsQuery = "
        SELECT *
        FROM trip_detail
        WHERE trip_id = :tripId
        ORDER BY date, start_time
    ";
    
    $detailsStmt = $pdo->prepare($detailsQuery);
    $detailsStmt->bindParam(':tripId', $tripId, PDO::PARAM_INT);
    $detailsStmt->execute();
    $details = $detailsStmt->fetchAll(PDO::FETCH_ASSOC);
    
    // 獲取參與者信息
    $participantsQuery = "
        SELECT tp.participant_id, tp.user_id, tp.status, u.username
        FROM trip_participants tp
        JOIN users u ON tp.user_id = u.user_id
        WHERE tp.trip_id = :tripId
    ";
    
    $participantsStmt = $pdo->prepare($participantsQuery);
    $participantsStmt->bindParam(':tripId', $tripId, PDO::PARAM_INT);
    $participantsStmt->execute();
    $participants = $participantsStmt->fetchAll(PDO::FETCH_ASSOC);
    
    // 返回完整的行程信息
    echo json_encode([
        'trip' => $trip,
        'details' => $details,
        'participants' => $participants
    ]);
    
} catch(PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
}
?>