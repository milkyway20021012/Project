<?php
// C:\xampp\htdocs\tripmate\api\trips-paged.php

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');
header('Access-Control-Allow-Headers: Content-Type');

// 資料庫連接參數
$host = 'localhost';
$dbname = 'tripmate';
$username = 'root';
$password = '';

// 獲取分頁和排序參數
$page = isset($_GET['page']) ? intval($_GET['page']) : 1;
$limit = isset($_GET['limit']) ? intval($_GET['limit']) : 10;
$sort = isset($_GET['sort']) ? $_GET['sort'] : 'created_at';
$order = isset($_GET['order']) ? $_GET['order'] : 'DESC';

// 獲取篩選參數
$area = isset($_GET['area']) ? $_GET['area'] : '';
$tag = isset($_GET['tag']) ? $_GET['tag'] : '';
$startDate = isset($_GET['startDate']) ? $_GET['startDate'] : '';
$endDate = isset($_GET['endDate']) ? $_GET['endDate'] : '';
// 獲取搜尋參數
$search = isset($_GET['search']) ? $_GET['search'] : '';

// 驗證和清理參數
if ($page < 1) $page = 1;
if ($limit < 1 || $limit > 50) $limit = 10;

// 計算偏移量
$offset = ($page - 1) * $limit;

// 允許的排序字段
$allowedSorts = ['trip_id', 'title', 'start_date', 'end_date', 'area', 'created_at', 'view_count'];
if (!in_array($sort, $allowedSorts)) {
    $sort = 'created_at';
}

// 排序方向
$order = strtoupper($order) === 'ASC' ? 'ASC' : 'DESC';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // 建立查詢條件
    $conditions = [];
    $params = [];
    
    if (!empty($area)) {
        $conditions[] = "t.area = :area";
        $params[':area'] = $area;
    }
    
    if (!empty($tag)) {
        $conditions[] = "t.tags LIKE :tag";
        $params[':tag'] = '%' . $tag . '%';
    }
    
    if (!empty($startDate)) {
        $conditions[] = "t.start_date >= :startDate";
        $params[':startDate'] = $startDate;
    }
    
    if (!empty($endDate)) {
        $conditions[] = "t.end_date <= :endDate";
        $params[':endDate'] = $endDate;
    }
    
    // 添加搜尋條件
    if (!empty($search)) {
        $conditions[] = "(t.title LIKE :search OR t.description LIKE :search OR t.area LIKE :search OR t.tags LIKE :search)";
        $params[':search'] = '%' . $search . '%';
    }
    
    $whereClause = !empty($conditions) ? "WHERE " . implode(" AND ", $conditions) : "";
    
    // 計算符合條件的總行程數
    $countQuery = "SELECT COUNT(*) as total FROM trip t $whereClause";
    $countStmt = $pdo->prepare($countQuery);
    foreach ($params as $key => $value) {
        $countStmt->bindValue($key, $value);
    }
    $countStmt->execute();
    $totalCount = $countStmt->fetch(PDO::FETCH_ASSOC)['total'];
    
    // 計算總頁數
    $totalPages = ceil($totalCount / $limit);
    
    // 獲取當前頁的行程
    $sql = "
        SELECT t.*,
              u.username as creator_name,
              (SELECT COUNT(*) FROM trip_participants tp WHERE tp.trip_id = t.trip_id AND tp.status = 'accepted') as total_participants
        FROM trip t
        JOIN users u ON t.user_id = u.user_id
        $whereClause
        ORDER BY t.$sort $order
        LIMIT :offset, :limit
    ";
    
    $stmt = $pdo->prepare($sql);
    foreach ($params as $key => $value) {
        $stmt->bindValue($key, $value);
    }
    $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    $trips = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // 返回完整的分頁信息和數據
    echo json_encode([
        'data' => $trips,
        'pagination' => [
            'total' => $totalCount,
            'total_pages' => $totalPages,
            'current_page' => $page,
            'limit' => $limit
        ]
    ]);
    
} catch(PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
}
?>