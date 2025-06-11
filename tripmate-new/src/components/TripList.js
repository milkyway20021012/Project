// components/TripList.js - 修正 API 路徑版本
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TripDetail from './TripDetail';
import './TripList.css';

const TripList = () => {
    const [trips, setTrips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pagination, setPagination] = useState({
        total: 0,
        total_pages: 0,
        current_page: 1,
        limit: 10
    });
    const [selectedTrip, setSelectedTrip] = useState(null);
    const [tripDetails, setTripDetails] = useState({
        trip: null,
        details: [],
        participants: []
    });

    // 排序狀態
    const [sortField, setSortField] = useState('created_at');
    const [sortOrder, setSortOrder] = useState('DESC');

    // 篩選選項
    const [areas, setAreas] = useState([]);
    const [tags, setTags] = useState([]);

    // 篩選狀態
    const [selectedArea, setSelectedArea] = useState('');
    const [selectedTag, setSelectedTag] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [timeFilter, setTimeFilter] = useState('all');

    // UI狀態
    const [viewMode, setViewMode] = useState('table'); // 'table' 或 'card'

    useEffect(() => {
        // 獲取篩選選項
        fetchFilterOptions();

        // 獲取行程數據
        fetchTrips(
            pagination.current_page,
            pagination.limit,
            sortField,
            sortOrder,
            selectedArea,
            selectedTag,
            startDate,
            endDate,
            searchTerm
        );
    }, [pagination.current_page, sortField, sortOrder, selectedArea, selectedTag, startDate, endDate, searchTerm]);

    const fetchFilterOptions = async () => {
        try {
            const response = await axios.get(`/api/get-filters`);
            setAreas(response.data.areas);
            setTags(response.data.tags);
        } catch (err) {
            console.error('Error fetching filter options:', err);
        }
    };

    const fetchTrips = async (page, limit, sort, order, area, tag, startDate, endDate, search) => {
        setLoading(true);
        try {
            const response = await axios.get(`/api/trips-paged`, {
                params: {
                    page,
                    limit,
                    sort,
                    order,
                    area,
                    tag,
                    startDate,
                    endDate,
                    search
                }
            });

            setTrips(response.data.data);
            setPagination(response.data.pagination);
            setError(null);
        } catch (err) {
            console.error('Error fetching trips:', err);
            setError('加載行程失敗，請稍後再試。');
        } finally {
            setLoading(false);
        }
    };

    const handlePageChange = (newPage) => {
        if (newPage >= 1 && newPage <= pagination.total_pages) {
            setPagination({
                ...pagination,
                current_page: newPage
            });
        }
    };

    const handleSort = (field) => {
        if (field === sortField) {
            // 如果點擊的是當前排序字段，則切換排序方向
            setSortOrder(sortOrder === 'ASC' ? 'DESC' : 'ASC');
        } else {
            // 如果是新字段，則設置為降序
            setSortField(field);
            setSortOrder('DESC');
        }
    };

    const handleFilterChange = (e) => {
        const { name, value } = e.target;

        // 更新對應的篩選狀態
        switch (name) {
            case 'area':
                setSelectedArea(value);
                break;
            case 'tag':
                setSelectedTag(value);
                break;
            case 'startDate':
                setStartDate(value);
                break;
            case 'endDate':
                setEndDate(value);
                break;
            default:
                break;
        }

        // 重置到第一頁
        setPagination({
            ...pagination,
            current_page: 1
        });
    };

    // 搜尋處理函數
    const handleSearchChange = (e) => {
        setSearchTerm(e.target.value);
    };

    const handleSearch = () => {
        // 重置到第一頁
        setPagination({
            ...pagination,
            current_page: 1
        });
        setIsSearching(true);

        // 使用當前的搜尋條件重新獲取行程數據
        fetchTrips(
            1,
            pagination.limit,
            sortField,
            sortOrder,
            selectedArea,
            selectedTag,
            startDate,
            endDate,
            searchTerm
        );
    };

    // 處理時間段篩選
    const handleTimeFilterChange = (filter) => {
        setTimeFilter(filter);

        let startDateFilter = '';
        let endDateFilter = '';

        const today = new Date();

        if (filter === 'week') {
            // 本週
            const firstDayOfWeek = new Date(today);
            firstDayOfWeek.setDate(today.getDate() - today.getDay());
            startDateFilter = firstDayOfWeek.toISOString().split('T')[0];
        } else if (filter === 'month') {
            // 本月
            const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
            startDateFilter = firstDayOfMonth.toISOString().split('T')[0];
        } else if (filter === 'season') {
            // 本季度
            const currentMonth = today.getMonth();
            const firstMonthOfQuarter = Math.floor(currentMonth / 3) * 3;
            const firstDayOfQuarter = new Date(today.getFullYear(), firstMonthOfQuarter, 1);
            startDateFilter = firstDayOfQuarter.toISOString().split('T')[0];
        }

        setStartDate(startDateFilter);
        setEndDate(endDateFilter);

        // 重置到第一頁
        setPagination({
            ...pagination,
            current_page: 1
        });

        // 使用時間篩選獲取數據
        fetchTrips(
            1,
            pagination.limit,
            sortField,
            sortOrder,
            selectedArea,
            selectedTag,
            startDateFilter,
            endDateFilter,
            searchTerm
        );
    };

    // 處理視圖模式切換
    const handleViewModeChange = (mode) => {
        setViewMode(mode);
    };

    // 合併功能的 handleResetFilters 函數
    const handleResetFilters = () => {
        setSelectedArea('');
        setSelectedTag('');
        setStartDate('');
        setEndDate('');
        setSearchTerm('');
        setTimeFilter('all');
        setIsSearching(false);
        setPagination({
            ...pagination,
            current_page: 1
        });

        // 重置所有條件後重新獲取數據
        fetchTrips(1, pagination.limit, sortField, sortOrder, '', '', '', '', '');
    };

    const handleTripClick = async (tripId) => {
        console.log('Trip clicked:', tripId);
        try {
            // 增加瀏覽次數
            await axios.post(`/api/increment-view`, { tripId });

            // 獲取行程詳情
            const response = await axios.get(`/api/trip-detail`, {
                params: { id: tripId }
            });

            console.log('Trip details response:', response.data);

            // 設置行程詳情
            setTripDetails(response.data);
            setSelectedTrip(tripId);

            // 重新加載行程列表（更新瀏覽次數）
            fetchTrips(
                pagination.current_page,
                pagination.limit,
                sortField,
                sortOrder,
                selectedArea,
                selectedTag,
                startDate,
                endDate,
                searchTerm
            );
        } catch (err) {
            console.error('Error fetching trip details:', err);
        }
    };

    const handleCloseDetail = () => {
        setSelectedTrip(null);
    };

    const formatDate = (dateString) => {
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(dateString).toLocaleDateString(undefined, options);
    };

    const renderSortIcon = (field) => {
        if (field !== sortField) return null;
        return sortOrder === 'ASC' ? ' ↑' : ' ↓';
    };

    // 渲染時間段篩選標籤
    const renderTimeFilterTabs = () => {
        return (
            <div className="time-filter-tabs">
                <button
                    className={`time-filter-tab ${timeFilter === 'all' ? 'active' : ''}`}
                    onClick={() => handleTimeFilterChange('all')}
                >
                    全部
                </button>
                <button
                    className={`time-filter-tab ${timeFilter === 'week' ? 'active' : ''}`}
                    onClick={() => handleTimeFilterChange('week')}
                >
                    本週熱門
                </button>
                <button
                    className={`time-filter-tab ${timeFilter === 'month' ? 'active' : ''}`}
                    onClick={() => handleTimeFilterChange('month')}
                >
                    本月熱門
                </button>
                <button
                    className={`time-filter-tab ${timeFilter === 'season' ? 'active' : ''}`}
                    onClick={() => handleTimeFilterChange('season')}
                >
                    本季熱門
                </button>
            </div>
        );
    };

    // 渲染視圖切換按鈕
    const renderViewToggle = () => {
        return (
            <div className="view-toggle">
                <button
                    className={viewMode === 'table' ? 'active' : ''}
                    onClick={() => handleViewModeChange('table')}
                >
                    <span>表格視圖</span>
                </button>
                <button
                    className={viewMode === 'card' ? 'active' : ''}
                    onClick={() => handleViewModeChange('card')}
                >
                    <span>卡片視圖</span>
                </button>
            </div>
        );
    };

    const renderFilterPanel = () => {
        return (
            <div className="filter-panel">
                <h3>篩選選項</h3>

                {renderTimeFilterTabs()}

                <div className="filter-row">
                    {/* 搜尋欄位 */}
                    <div className="filter-group search-group">
                        <label htmlFor="search">搜尋行程</label>
                        <div className="search-input-container">
                            <input
                                type="text"
                                id="search"
                                name="search"
                                value={searchTerm}
                                onChange={handleSearchChange}
                                placeholder="輸入關鍵字搜尋行程..."
                                onKeyPress={(e) => {
                                    if (e.key === 'Enter') {
                                        handleSearch();
                                    }
                                }}
                            />
                            <button
                                className="search-button"
                                onClick={handleSearch}
                            >
                                搜尋
                            </button>
                        </div>
                    </div>
                </div>

                <div className="filter-row">
                    <div className="filter-group">
                        <label htmlFor="area">地區</label>
                        <select
                            id="area"
                            name="area"
                            value={selectedArea}
                            onChange={handleFilterChange}
                        >
                            <option value="">所有地區</option>
                            {areas.map(area => (
                                <option key={area} value={area}>{area}</option>
                            ))}
                        </select>
                    </div>

                    <div className="filter-group">
                        <label htmlFor="tag">標籤</label>
                        <select
                            id="tag"
                            name="tag"
                            value={selectedTag}
                            onChange={handleFilterChange}
                        >
                            <option value="">所有標籤</option>
                            {tags.map(tag => (
                                <option key={tag} value={tag}>{tag}</option>
                            ))}
                        </select>
                    </div>

                    <div className="filter-group date-group">
                        <label>日期範圍</label>
                        <div className="date-inputs">
                            <div className="date-input-wrapper">
                                <label htmlFor="startDate">開始日期</label>
                                <input
                                    type="date"
                                    id="startDate"
                                    name="startDate"
                                    value={startDate}
                                    onChange={handleFilterChange}
                                />
                            </div>
                            <div className="date-input-wrapper">
                                <label htmlFor="endDate">結束日期</label>
                                <input
                                    type="date"
                                    id="endDate"
                                    name="endDate"
                                    value={endDate}
                                    onChange={handleFilterChange}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="filter-actions">
                    <button
                        className="reset-button"
                        onClick={handleResetFilters}
                    >
                        重置篩選
                    </button>
                </div>
            </div>
        );
    };

    const renderPagination = () => {
        const { current_page, total_pages } = pagination;

        if (total_pages === 0) return null;

        // 計算要顯示的頁碼範圍
        let startPage = Math.max(1, current_page - 2);
        let endPage = Math.min(total_pages, startPage + 4);

        if (endPage - startPage < 4 && total_pages > 5) {
            startPage = Math.max(1, endPage - 4);
        }

        const pageNumbers = [];
        for (let i = startPage; i <= endPage; i++) {
            pageNumbers.push(i);
        }

        return (
            <div className="pagination">
                <button
                    onClick={() => handlePageChange(1)}
                    disabled={current_page === 1}
                    className="pagination-button"
                >
                    &laquo;
                </button>

                <button
                    onClick={() => handlePageChange(current_page - 1)}
                    disabled={current_page === 1}
                    className="pagination-button"
                >
                    &lt;
                </button>

                {pageNumbers.map(number => (
                    <button
                        key={number}
                        onClick={() => handlePageChange(number)}
                        className={`pagination-button ${current_page === number ? 'active' : ''}`}
                    >
                        {number}
                    </button>
                ))}

                <button
                    onClick={() => handlePageChange(current_page + 1)}
                    disabled={current_page === total_pages}
                    className="pagination-button"
                >
                    &gt;
                </button>

                <button
                    onClick={() => handlePageChange(total_pages)}
                    disabled={current_page === total_pages}
                    className="pagination-button"
                >
                    &raquo;
                </button>

                <span className="pagination-info">
                    第 {current_page}/{total_pages} 頁，共 {pagination.total} 筆
                </span>
            </div>
        );
    };

    const renderTripTable = () => {
        if (loading) return <div className="loading">加載中...</div>;
        if (error) return <div className="error">{error}</div>;
        if (trips.length === 0) return <div className="no-trips">沒有找到符合條件的行程。</div>;

        return (
            <div className="trip-table-container">
                <table className="trip-table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th onClick={() => handleSort('title')}>
                                行程標題 {renderSortIcon('title')}
                            </th>
                            <th onClick={() => handleSort('start_date')}>
                                開始日期 {renderSortIcon('start_date')}
                            </th>
                            <th onClick={() => handleSort('end_date')}>
                                結束日期 {renderSortIcon('end_date')}
                            </th>
                            <th onClick={() => handleSort('area')}>
                                地區 {renderSortIcon('area')}
                            </th>
                            <th>標籤</th>
                            <th onClick={() => handleSort('view_count')}>
                                瀏覽次數 {renderSortIcon('view_count')}
                            </th>
                            <th>參與者數量</th>
                            <th>創建者</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trips.map((trip, index) => {
                            // 計算實際排名，考慮分頁
                            const rank = (pagination.current_page - 1) * pagination.limit + index + 1;

                            return (
                                <tr
                                    key={trip.trip_id}
                                    onClick={() => handleTripClick(trip.trip_id)}
                                    className="trip-row"
                                >
                                    <td>
                                        <div className={`rank rank-${rank}`}>
                                            {rank}
                                        </div>
                                    </td>
                                    <td className="trip-title">{trip.title}</td>
                                    <td>{formatDate(trip.start_date)}</td>
                                    <td>{formatDate(trip.end_date)}</td>
                                    <td>{trip.area}</td>
                                    <td>
                                        {trip.tags && (
                                            <div className="trip-tags">
                                                {trip.tags.split(',').map((tag, i) => (
                                                    <span key={i} className="trip-tag">{tag.trim()}</span>
                                                ))}
                                            </div>
                                        )}
                                    </td>
                                    <td>{trip.view_count || 0}</td>
                                    <td>{trip.total_participants || 0}</td>
                                    <td>{trip.creator_name}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        );
    };

    // 卡片視圖渲染
    const renderCardView = () => {
        if (loading) return <div className="loading">加載中...</div>;
        if (error) return <div className="error">{error}</div>;
        if (trips.length === 0) return <div className="no-trips">沒有找到符合條件的行程。</div>;

        return (
            <div className="trip-card-view">
                {trips.map((trip, index) => {
                    // 計算實際排名，考慮分頁
                    const rank = (pagination.current_page - 1) * pagination.limit + index + 1;

                    return (
                        <div
                            key={trip.trip_id}
                            className="trip-card"
                            onClick={() => handleTripClick(trip.trip_id)}
                        >
                            <div className="trip-card-header">
                                <div className="trip-card-title">{trip.title}</div>
                                <div className={`trip-card-rank rank rank-${rank}`}>{rank}</div>
                            </div>
                            <div className="trip-card-content">
                                <div className="trip-card-info">
                                    <span className="trip-card-area">{trip.area}</span>
                                </div>
                                <div className="trip-card-info">
                                    <span className="trip-card-date">
                                        {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
                                    </span>
                                </div>
                                {trip.description && (
                                    <div className="trip-card-description">
                                        {trip.description.length > 80
                                            ? trip.description.substring(0, 80) + '...'
                                            : trip.description}
                                    </div>
                                )}
                                {trip.tags && (
                                    <div className="trip-card-tags">
                                        {trip.tags.split(',').map((tag, i) => (
                                            <span key={i} className="trip-tag">{tag.trim()}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <div className="trip-card-footer">
                                <div className="trip-card-creator">由 {trip.creator_name} 創建</div>
                                <div className="trip-card-views">{trip.view_count || 0} 次瀏覽</div>
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="trip-list-container">
            <h2>行程排行榜</h2>
            {renderFilterPanel()}

            <div className="list-header">
                {renderViewToggle()}
            </div>

            {viewMode === 'table' ? renderTripTable() : renderCardView()}
            {renderPagination()}

            {/* 行程詳情彈窗 */}
            {selectedTrip && (
                <TripDetail
                    trip={tripDetails.trip}
                    details={tripDetails.details}
                    participants={tripDetails.participants}
                    onClose={handleCloseDetail}
                />
            )}
        </div>
    );
};

export default TripList;