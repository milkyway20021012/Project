$(document).ready(function () {
    let apiURL = "travel_rank.php";
    let currentCategoryId = null;
    let currentTrips = [];
    let totalPages = 1; // 最大頁數

    // 取得分類
    $.getJSON(`${apiURL}?action=get_categories`, function (categories) {
        let categoryHtml = "";
        categories.forEach(category => {
            categoryHtml += `<div class="category" data-id="${category.id}">${category.name}</div>`;
            if (category.name === "熱門景點") {
                currentCategoryId = category.id;
            }
        });
        $("#categories").html(categoryHtml);

        if (currentCategoryId) {
            $("#category-title").text("熱門景點");
            loadTrips(currentCategoryId, 1); // 默認載入第1頁
        }
    });

    // 顯示分類下的行程
    $(document).on("click", ".category", function () {
        currentCategoryId = $(this).data("id");
        let categoryName = $(this).text();
        $("#category-title").text(categoryName);
        loadTrips(currentCategoryId, 1); // 默認載入第1頁
    });

    // 顯示行程
    function loadTrips(categoryId, page) {
        let url = `${apiURL}?action=get_trips&category_id=${categoryId}&page=${page}`;

        $.getJSON(url, function (data) {
            currentTrips = data.trips;
            totalPages = data.totalPages; // 更新最大頁數
            displayTrips(currentTrips);
            displayPagination(page); // 顯示分頁
        });
    }

    // 顯示行程
    function displayTrips(trips) {
        let tripHtml = trips.length > 0 ? "" : "<h3 class='trip-category'>未找到相關行程</h3>";
        trips.forEach(trip => {
            tripHtml += `<div class="trip-item" data-id="${trip.id}">
                            <span class="trip-info">${trip.name}</span>
                            <span class="trip-views">瀏覽次數: ${trip.views}</span>
                          </div>`;
        });
        $("#trips").hide().html(tripHtml).fadeIn();
    }

    // 顯示分頁
    function displayPagination(currentPage) {
        let paginationHtml = "";
        for (let i = 1; i <= totalPages; i++) {
            paginationHtml += `<span class="page-link" data-page="${i}">${i}</span> `;
        }
        $("#pagination").html(paginationHtml);

        // 高亮當前頁碼
        $(".page-link").removeClass("active");
        $(`.page-link[data-page="${currentPage}"]`).addClass("active");
    }

    // 點擊分頁按鈕
    $(document).on("click", ".page-link", function () {
        let page = $(this).data("page");
        loadTrips(currentCategoryId, page); // 根據頁碼載入行程
    });

    // 點擊行程後，瀏覽次數自動+1
    $(document).on("click", ".trip-item", function () {
        let tripId = $(this).data("id");
        let viewsElement = $(this).find(".trip-views");

        // 發送 AJAX 請求，更新該行程的瀏覽次數
        $.post(`${apiURL}?action=increment_views`, { trip_id: tripId }, function (response) {
            if (response.success) {
                let currentViews = parseInt(viewsElement.text().replace("瀏覽次數: ", "")) || 0;
                viewsElement.text(`瀏覽次數: ${currentViews + 1}`);
            }
        }, "json");
    });

    // 即時搜索
    $("#search").on("input", function () {
        let query = $(this).val().trim().toLowerCase();
        filterTrips(query);
    });

    // 根據搜尋關鍵字過濾行程
    function filterTrips(query) {
        if (query === "") {
            displayTrips(currentTrips);  // 若搜尋框為空，顯示所有行程
        } else {
            let filteredTrips = currentTrips.filter(trip => trip.name.toLowerCase().includes(query));
            displayTrips(filteredTrips);  // 顯示篩選後的行程
        }
    }
});