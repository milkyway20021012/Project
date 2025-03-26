<?php
$servername = "localhost"; // 你的資料庫伺服器
$username = "root"; // 你的資料庫帳號
$password = ""; // 你的資料庫密碼
$dbname = "tripmate"; // 資料庫名稱

// 建立資料庫連線
$conn = new mysqli($servername, $username, $password, $dbname);

// 檢查連線是否成功
if ($conn->connect_error) {
    die("連線失敗：" . $conn->connect_error);
}

// 取得所有地區列表（去重）
$area_result = $conn->query("SELECT DISTINCT area FROM trip ORDER BY area ASC");
$areas = [];
while ($row = $area_result->fetch_assoc()) {
    $areas[] = $row['area'];
}

// 取得所有標籤列表（去重，並拆分標籤）
$tags_result = $conn->query("SELECT DISTINCT tags FROM trip");
$tags_set = [];
while ($row = $tags_result->fetch_assoc()) {
    $tag_list = explode(",", $row['tags']); // 假設標籤以逗號分隔
    foreach ($tag_list as $tag) {
        $trimmed_tag = trim($tag);
        if (!empty($trimmed_tag)) {
            $tags_set[$trimmed_tag] = true;
        }
    }
}
$tags_list = array_keys($tags_set);
sort($tags_list);

// 設定分頁變數
$limit = 6; // 每頁顯示 7 筆
$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$offset = ($page - 1) * $limit;
$search = isset($_GET['search']) ? trim($_GET['search']) : "";
$start_date = isset($_GET['start_date']) ? $_GET['start_date'] : "";
$end_date = isset($_GET['end_date']) ? $_GET['end_date'] : "";
$area = isset($_GET['area']) ? $_GET['area'] : "";
$tags = isset($_GET['tags']) ? $_GET['tags'] : "";
$budget = isset($_GET['budget']) ? $_GET['budget'] : "";

// 建立 SQL 條件
$whereClauses = [];
if (!empty($search)) {
    $whereClauses[] = "title LIKE '%" . $conn->real_escape_string($search) . "%'";
}
if (!empty($start_date) && !empty($end_date)) {
    // 強制 start_date 和 end_date 必須完全符合
    $whereClauses[] = "start_date = '" . $conn->real_escape_string($start_date) . "' AND end_date = '" . $conn->real_escape_string($end_date) . "'";
}
if (!empty($area)) {
    $whereClauses[] = "area = '" . $conn->real_escape_string($area) . "'";
}
if (!empty($tags)) {
    $whereClauses[] = "tags LIKE '%" . $conn->real_escape_string($tags) . "%'";
}
if (!empty($budget)) {
    $whereClauses[] = "CAST(budget AS UNSIGNED) <= " . (int)$budget;
}

$whereClause = "";
if (!empty($whereClauses)) {
    $whereClause = "WHERE " . implode(" AND ", $whereClauses);
}

// 取得符合條件的總行程數量
$total_result = $conn->query("SELECT COUNT(*) AS total FROM trip $whereClause");
$total_row = $total_result->fetch_assoc();
$total_trips = $total_row['total'];
$total_pages = ceil($total_trips / $limit);

// SQL 查詢：取得符合條件的行程
$sql = "SELECT trip_id, title, view_count FROM trip $whereClause ORDER BY view_count DESC LIMIT $limit OFFSET $offset";
$result = $conn->query($sql);

?>
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>熱門行程排行榜</title>
    <link rel="stylesheet" href="styles.css">
    <script defer src="script.js"></script>
    <!-- 引入 Select2 的 CSS -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css" rel="stylesheet" />
    <!-- 引入 jQuery 和 Select2 的 JS -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js"></script>
</head>
<body>
    <div class="container">
        <h2>熱門行程排行榜</h2>
        <div class="filters">
            <input type="text" id="search" class="filter-input" placeholder="搜尋行程..." value="<?php echo htmlspecialchars($search); ?>">
            <div class="date-range">
                <label>開始日期：</label>
                <input type="date" id="start_date" class="filter-input" value="<?php echo htmlspecialchars($start_date); ?>">
                <label>結束日期：</label>
                <input type="date" id="end_date" class="filter-input" value="<?php echo htmlspecialchars($end_date); ?>">
            </div>
            <label for="area">選擇地區：</label>
            <select id="area" class="filter-input">
                <option value="">所有地區</option>
                <?php foreach ($areas as $a) {
                    echo "<option value='" . htmlspecialchars($a) . "' " . ($a == $area ? "selected" : "") . ">" . htmlspecialchars($a) . "</option>";
                } ?>
            </select>

            <label for="tags">選擇標籤：</label>
            <select id="tags" class="filter-input">
                <option value="">所有標籤</option>
                <?php foreach ($tags_list as $t) {
                    echo "<option value='" . htmlspecialchars($t) . "' " . ($t == $tags ? "selected" : "") . ">" . htmlspecialchars($t) . "</option>";
                } ?>
            </select>
            <label for="budget">最大預算：</label>
            <input type="number" id="budget" class="filter-input" placeholder="最大預算..." value="<?php echo htmlspecialchars($budget); ?>">
            <button id="clear-filters" class="clear-filters-btn">清除篩選</button>
        </div>
        <!-- 加載指示器 -->
        <div id="loading-indicator" class="loading-indicator" style="display: none;">
            <div class="spinner"></div>
        </div>

        <!-- 行程清單 -->
        <ul id="trip-list">
            <?php if ($result->num_rows > 0) {
                while($row = $result->fetch_assoc()) {
                    echo "<li data-trip-id='" . $row['trip_id'] . "'><a href='#'>" . htmlspecialchars($row['title']) . "</a><span class='view-count'>瀏覽次數: " . $row['view_count'] . "</span></li>";
                }
            } else {
                echo "<li>目前沒有行程資料</li>";
            } ?>
        </ul>

        <!-- 分頁區域 -->
        <div class="pagination">
            <?php for ($i = 1; $i <= $total_pages; $i++) {
                echo "<a href='?search=" . urlencode($search) . "&start_date=$start_date&end_date=$end_date&area=$area&tags=$tags&budget=$budget&page=$i' class='" . ($i == $current_page ? 'active' : '') . "'>$i</a>";
            } ?>
        </div>
    </div>

    <!-- Modal for trip details -->
    <div id="tripModal" class="modal">
        <div class="modal-content">
            <span id="closeModal" class="close">&times;</span>
            <h2 id="tripTitle">Trip Title</h2>
            <p id="tripDescription">Trip description goes here...</p>
            <p id="tripDetails">Additional details about the trip...</p>
        </div>
    </div>
</body>
</html>
<?php
$conn->close();
?>