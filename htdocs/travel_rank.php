<?php
header("Content-Type: application/json");
$conn = new mysqli("localhost", "root", "", "travel_rank");

if ($conn->connect_error) {
    die(json_encode(["error" => "資料庫連線失敗"]));
}

$action = isset($_GET['action']) ? $_GET['action'] : '';

if ($action == 'get_categories') {
    $query = "SELECT * FROM categories ORDER BY id";
    $result = $conn->query($query);
    $categories = [];

    while ($row = $result->fetch_assoc()) {
        if (is_null($row['parent_id'])) {
            $categories[$row['id']] = [
                'id' => $row['id'],
                'name' => $row['name'],
                'sub_categories' => []
            ];
        } else {
            if (isset($categories[$row['parent_id']])) {
                $categories[$row['parent_id']]['sub_categories'][] = [
                    'id' => $row['id'],
                    'name' => $row['name']
                ];
            }
        }
    }

    echo json_encode(array_values($categories));
}

// 取得行程資訊，支援搜尋
elseif ($action == 'get_trips') {
    $category_id = isset($_GET['category_id']) ? intval($_GET['category_id']) : null;
    $search_query = isset($_GET['query']) ? "%" . $_GET['query'] . "%" : null;

    $query = "SELECT * FROM trips WHERE 1=1";
    $params = [];
    $types = "";

    if ($category_id) {
        $query .= " AND (category_id = ? OR category_id IN (SELECT id FROM categories WHERE parent_id = ?))";
        $params[] = $category_id;
        $params[] = $category_id;
        $types .= "ii";
    }

    if ($search_query) {
        $query .= " AND name LIKE ?";
        $params[] = $search_query;
        $types .= "s";
    }

    $stmt = $conn->prepare($query);
    if (!empty($params)) {
        $stmt->bind_param($types, ...$params);
    }
    
    $stmt->execute();
    $result = $stmt->get_result();

    $trips = [];
    while ($row = $result->fetch_assoc()) {
        $trips[] = $row;
    }

    echo json_encode(["trips" => $trips]);
}

$conn->close();
?>