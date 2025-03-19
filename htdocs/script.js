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
