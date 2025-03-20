$(document).ready(function() {
    // 為地區選擇器和標籤選擇器啟用 Select2
    $('#area').select2({
        placeholder: '選擇地區', // 顯示在下拉選單中，提示使用者選擇
        allowClear: true // 允許清除選擇
    });

    $('#tags').select2({
        placeholder: '選擇標籤',
        allowClear: true
    });

    // 當選擇地區或標籤時即時觸發篩選
    $('#area, #tags').on('change', function() {
        updateFilters();
    });
});

// 更新篩選器（會觸發頁面更新，並將篩選條件作為 URL 參數）
function updateFilters() {
    // 獲取篩選條件
    let area = $('#area').val();
    let tags = $('#tags').val();

    // 構建查詢字串
    let params = new URLSearchParams(window.location.search);
    if (area) {
        params.set('area', area);  // 更新地區篩選條件
    } else {
        params.delete('area');
    }

    if (tags) {
        params.set('tags', tags);  // 更新標籤篩選條件
    } else {
        params.delete('tags');
    }

    // 重新載入頁面並帶上篩選參數
    window.location.href = "?" + params.toString();
}

// 以下是您的原有程式碼，為了不修改原來的邏輯，我保持不變
document.addEventListener("DOMContentLoaded", function () {
    const filters = ["search", "start_date", "end_date", "area", "tags", "budget"];
    const budgetInput = document.getElementById("budget");

    let filterTimeout;
    let budgetTimeout;
    let searchTimeout;

    // 監聽一般篩選條件（即時觸發）
    filters.forEach(filter => {
        const input = document.getElementById(filter);
        if (filter !== "budget" && filter !== "search") {
            input.addEventListener("input", updateFilters); // 立即觸發篩選
        }
    });

    // 監聽搜尋框，避免輸入後馬上篩選
    const searchInput = document.getElementById("search");
    searchInput.addEventListener("input", function () {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(updateFilters, 1000); // 停止 1 秒後觸發篩選
    });

    // 監聽預算輸入框，只有在使用者停止輸入 1 秒後觸發
    budgetInput.addEventListener("input", function () {
        clearTimeout(budgetTimeout);
        budgetTimeout = setTimeout(updateFilters, 1000); // 停止 1 秒後觸發篩選
    });

    function updateFilters() {
        let params = new URLSearchParams(window.location.search);
        
        // 保留目前的頁碼
        const currentPage = params.get("page") || 1;

        filters.forEach(filter => {
            let value = document.getElementById(filter).value.trim();
            if (value !== "") {
                params.set(filter, value);
            } else {
                params.delete(filter); // 如果輸入為空，則從 URL 參數中移除
            }
        });

        // 保留頁碼參數
        params.set("page", currentPage);

        window.location.href = "?" + params.toString();
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const filters = ["search", "start_date", "end_date", "area", "tags", "budget"];
    const searchInput = document.getElementById("search");
    const budgetInput = document.getElementById("budget");

    // 防抖處理
    let searchTimeout;
    let budgetTimeout;

    // 監聽篩選器變動
    filters.forEach(filter => {
        const input = document.getElementById(filter);
        if (filter !== "budget" && filter !== "search") {
            input.addEventListener("input", updateFilters);
        }
    });

    // 搜尋框防抖
    searchInput.addEventListener("input", function () {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(updateFilters, 1000);
    });

    // 預算輸入框防抖
    budgetInput.addEventListener("input", function () {
        clearTimeout(budgetTimeout);
        budgetTimeout = setTimeout(updateFilters, 1000);
    });

    // 更新篩選條件
    function updateFilters() {
        showLoadingIndicator();
        let params = new URLSearchParams(window.location.search);
        filters.forEach(filter => {
            let value = document.getElementById(filter).value.trim();
            if (value !== "") {
                params.set(filter, value);
            } else {
                params.delete(filter);
            }
        });

        params.set("page", 1); // 重設頁碼
        window.location.href = "?" + params.toString();
    }

    // 顯示加載指示器
    function showLoadingIndicator() {
        document.getElementById("loading-indicator").style.display = "block";
    }

    // 隱藏加載指示器
    function hideLoadingIndicator() {
        document.getElementById("loading-indicator").style.display = "none";
    }

    // 清除篩選器
    document.getElementById("clear-filters").addEventListener("click", function() {
        filters.forEach(filter => {
            const input = document.getElementById(filter);
            if (input) {
                input.value = "";
            }
        });
        updateFilters();
    });
});