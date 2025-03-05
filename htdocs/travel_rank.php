<?php
// 連接資料庫
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "travel_rank";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die("≥s±µ•¢±—: " . $conn->connect_error);
}

$action = $_GET['action'] ?? null;

if ($action == 'get_categories') {
    // 取得所有分類
    $result = $conn->query("SELECT id, name FROM categories");
    $categories = $result->fetch_all(MYSQLI_ASSOC);
    echo json_encode($categories);
} elseif ($action == 'get_trips') {
    // 取得某個分類的行程
    $category_id = $_GET['category_id'] ?? 1;
    $page = $_GET['page'] ?? 1; // 頁碼（默認第一頁）
    $perPage = 10; // 每頁顯示10個行程
    $offset = ($page - 1) * $perPage; // 計算偏移量

    // 獲取該分類下的總行程數量
    $stmt = $conn->prepare("SELECT COUNT(*) AS total FROM trips WHERE category_id = ?");
    $stmt->bind_param("i", $category_id);
    $stmt->execute();
    $result = $stmt->get_result();
    $totalTrips = $result->fetch_assoc()['total']; // 總行程數量

    // 計算最大頁數
    $totalPages = ceil($totalTrips / $perPage);

    // 取得當前頁面對應的行程
    $stmt = $conn->prepare("SELECT id, name, views FROM trips WHERE category_id = ? ORDER BY views DESC LIMIT ?, ?");
    $stmt->bind_param("iii", $category_id, $offset, $perPage);
    $stmt->execute();
    $result = $stmt->get_result();
    $trips = $result->fetch_all(MYSQLI_ASSOC);

    // 使用名稱作為索引來保留瀏覽次數最多的行程
    $uniqueTrips = [];
    foreach ($trips as $trip) {
        $name = $trip['name'];
        if (!isset($uniqueTrips[$name]) || $uniqueTrips[$name]['views'] < $trip['views']) {
            $uniqueTrips[$name] = $trip;
        }
    }

    // 最終的行程列表就是唯一的並且瀏覽次數最高的行程
    $filteredTrips = array_values($uniqueTrips);

    // 返回行程和最大頁數
    echo json_encode([
        'trips' => $filteredTrips,
        'totalPages' => $totalPages
    ]);
} elseif ($action == 'increment_views') {
    // 增加行程的瀏覽次數
    $trip_id = $_POST['trip_id'] ?? null;
    if ($trip_id) {
        // 增加瀏覽次數
        $stmt = $conn->prepare("UPDATE trips SET views = views + 1 WHERE id = ?");
        $stmt->bind_param("i", $trip_id);
        if ($stmt->execute()) {
            echo json_encode(['success' => true]);
        } else {
            echo json_encode(['success' => false, 'message' => 'ßÛ∑s•¢±—']);
        }
        $stmt->close();
    } else {
        echo json_encode(['success' => false, 'message' => 'Ø §÷¶Êµ{ID']);
    }
}

$conn->close();
?>
