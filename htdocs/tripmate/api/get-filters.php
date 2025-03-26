<?php
// C:\xampp\htdocs\tripmate\api\get-filters.php

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');
header('Access-Control-Allow-Headers: Content-Type');

// 資料庫連接參數
$host = 'localhost';
$dbname = 'tripmate';
$username = 'root';
$password = '';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // 獲取所有地區
    $areaQuery = "SELECT DISTINCT area FROM trip ORDER BY area";
    $areaStmt = $pdo->query($areaQuery);
    $areas = $areaStmt->fetchAll(PDO::FETCH_COLUMN);
    
    // 獲取所有標籤
    $tagsQuery = "SELECT tags FROM trip WHERE tags IS NOT NULL AND tags != ''";
    $tagsStmt = $pdo->query($tagsQuery);
    $tagStrings = $tagsStmt->fetchAll(PDO::FETCH_COLUMN);
    
    // 處理標籤，可能存在逗號分隔的多個標籤
    $uniqueTags = [];
    foreach ($tagStrings as $tagString) {
        $tags = explode(',', $tagString);
        foreach ($tags as $tag) {
            $trimmedTag = trim($tag);
            if (!empty($trimmedTag) && !in_array($trimmedTag, $uniqueTags)) {
                $uniqueTags[] = $trimmedTag;
            }
        }
    }
    sort($uniqueTags);
    
    echo json_encode([
        'areas' => $areas,
        'tags' => $uniqueTags
    ]);
    
} catch(PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
}
?>