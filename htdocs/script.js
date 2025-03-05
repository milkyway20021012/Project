$(document).ready(function () {
    let apiURL = "travel_rank.php";
    let tripsPerPage = 10;
    let currentTrips = [];
    let filteredTrips = [];
    let totalPages = 1;
    let currentPage = 1;
    let currentCategoryId = null;

    // 取得分類（主分類與子分類）
    $.getJSON(`${apiURL}?action=get_categories`, function (categories) {
        let categoryHtml = "";
        categories.forEach(category => {
            categoryHtml += `<div class="category main-category" data-id="${category.id}">${category.name}</div>`;
            if (category.sub_categories.length > 0) {
                categoryHtml += `<div class="sub-category" id="sub-${category.id}" style="display: none;">`;
                category.sub_categories.forEach(subCategory => {
                    categoryHtml += `<div class="category sub-category" data-id="${subCategory.id}">${subCategory.name}</div>`;
                });
                categoryHtml += `</div>`;
            }
        });

        $("#categories").html(categoryHtml);
    });

    // 點擊主分類時載入所有行程
    $(document).on("click", ".main-category", function () {
        let categoryId = $(this).data("id");
        let categoryName = $(this).text();
        $("#category-title").text(categoryName);
        currentCategoryId = categoryId;
        $("#sub-" + categoryId).toggle(); // 展開或收起子類別
        loadTrips(categoryId, "");
    });

    // 點擊子分類時載入特定國家的行程
    $(document).on("click", ".sub-category", function () {
        let categoryId = $(this).data("id");
        let categoryName = $(this).text().replace("", "");
        $("#category-title").text(categoryName);
        currentCategoryId = categoryId;
        loadTrips(categoryId, "");
    });

    // 搜尋功能
    $("#search").on("input", function () {
        let query = $(this).val().trim();
        loadTrips(currentCategoryId, query);
    });

    function loadTrips(categoryId, query) {
        let url = `${apiURL}?action=get_trips`;
        if (categoryId) url += `&category_id=${categoryId}`;  // 確保 category_id 有被加入
        if (query) url += `&query=${query}`;
    
        $.getJSON(url, function (data) {
            filteredTrips = data.trips.filter(trip => trip.category_id == categoryId); // 確保只顯示屬於該類別的行程
            totalPages = Math.ceil(filteredTrips.length / tripsPerPage);
            currentPage = 1;
            displayTrips(getTripsByPage(currentPage));
            displayPagination();
        });
    }
    

    function getTripsByPage(page) {
        let start = (page - 1) * tripsPerPage;
        let end = start + tripsPerPage;
        return filteredTrips.slice(start, end);
    }

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

    function displayPagination() {
        let paginationHtml = "";
        let newTotalPages = Math.ceil(filteredTrips.length / tripsPerPage);
        totalPages = newTotalPages;
        for (let i = 1; i <= totalPages; i++) {
            paginationHtml += `<span class="page-link ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</span> `;
        }
        $("#pagination").html(paginationHtml);
    }

    // 點擊分頁切換
    $(document).on("click", ".page-link", function () {
        let selectedPage = parseInt($(this).attr("data-page"));
        if (selectedPage !== currentPage) {
            currentPage = selectedPage;
            displayTrips(getTripsByPage(currentPage));
            displayPagination();
        }
    });
});
