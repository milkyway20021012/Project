$(document).ready(function() {
    console.log('Document ready'); // 添加調試信息

    // 開啟 Modal
    function openModal(trip) {
        console.log('Opening modal with trip:', trip); // 添加調試信息
        $('#tripTitle').text(trip.title);
        $('#tripDescription').text(trip.description);
        $('#tripDetails').text('開始日期: ' + trip.start_date + ' 結束日期: ' + trip.end_date + '\n地區: ' + trip.area + '\n標籤: ' + trip.tags + '\n預算: ' + trip.budget);

        // 顯示 Modal
        $('#tripModal').css('display', 'block');
    }

    // 點擊行程項目
    $('ul#trip-list li').click(function() {
        const tripId = $(this).data('trip-id');  // 獲取行程 ID
        console.log('Trip ID:', tripId); // 添加調試信息

        // 使用 AJAX 請求行程詳細資料
        $.ajax({
            url: 'get_trip_details.php',  // 請求的 PHP 文件
            type: 'GET',
            data: { id: tripId },  // 傳遞 trip_id 參數
            success: function(response) {
                console.log('Response from server:', response); // 添加調試信息
                const trip = JSON.parse(response);  // 將回應轉換為 JSON 物件
                if (trip.error) {
                    alert(trip.error);  // 顯示錯誤訊息
                } else {
                    openModal(trip);  // 開啟 Modal 並顯示資料
                }
            },
            error: function() {
                alert('無法加載行程詳細資料');
            }
        });
    });
});