<?php
// 連接資料庫
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "travel_rank";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die("連接失敗: " . $conn->connect_error);
}

// 設定分類關鍵字
$category_keywords = [
    1 => ['101', '故宮', '日月潭', '墾丁'], // 熱門景點
    2 => ['櫻花', '賞櫻', '花季'], // 春季推薦
    3 => ['沙灘', '浮潛', '七星潭'], // 夏季推薦
    4 => ['楓葉', '賞楓', '秋景'], // 秋季推薦
    5 => ['滑雪', '雪山', '溫泉'], // 冬季推薦
    6 => ['遊樂園', '親子', '兒童', '傳藝'], // 親子旅遊
];

// 自動分類的函數
function getCategoryId($trip_name, $category_keywords) {
    foreach ($category_keywords as $category_id => $keywords) {
        foreach ($keywords as $keyword) {
            if (strpos($trip_name, $keyword) !== false) {
                return $category_id; // 找到對應的分類ID，直接返回
            }
        }
    }
    return null; // 如果沒有匹配到分類，則返回 null
}

// 當表單被提交
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST["trip_name"])) {
    $trip_name = $_POST["trip_name"]; // 使用者輸入的行程名稱
    $views = 0; // 預設瀏覽次數

    // 根據行程名稱自動分配分類
    $category_id = getCategoryId($trip_name, $category_keywords);

    if ($category_id) {
        // 插入數據到 trips 表
        $stmt = $conn->prepare("INSERT INTO trips (name, category_id, views) VALUES (?, ?, ?)");
        $stmt->bind_param("sii", $trip_name, $category_id, $views);

        if ($stmt->execute()) {
            echo "行程新增成功，分類已自動分配！";
        } else {
            echo "新增失敗：" . $stmt->error;
        }
        $stmt->close();
    } else {
        echo "無法自動分類，請手動選擇分類。";
    }
}

$conn->close();
?>

<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>行程排行</title>
    <link rel="stylesheet" href="style.css">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="script.js"></script>
</head>
<body>
    <!-- 新增排行榜標題 -->
    <h1 class="ranking-title">排行榜</h1>

    <div class="container">
        <div class="categories" id="categories">
            <!-- 類別會在這裡顯示 -->
        </div>
        <div class="trips-container">
            <h2 id="category-title">熱門景點</h2>
            <input type="text" id="search" class="search-input" placeholder="搜尋行程...">
            <div id="trips">
                <!-- 行程會在這裡顯示 -->
            </div>
            <div id="pagination" class="pagination">
                <!-- 分頁按鈕會顯示在這裡 -->
            </div>
        </div>
    </div>
</body>
</html>


