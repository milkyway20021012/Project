// components/TripRanking.js - 修正 API 路徑版本
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './TripRanking.css';

const TripRanking = () => {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('view'); // 'view', 'area', 'date'

  useEffect(() => {
    fetchTripRankings(activeTab);
  }, [activeTab]);

  const fetchTripRankings = async (rankingType) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/trip-rankings?type=${rankingType}`);
      setTrips(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching trip rankings:', err);
      setError('加載排行榜失敗，請稍後再試。');
    } finally {
      setLoading(false);
    }
  };

  const handleViewTrip = async (tripId) => {
    try {
      // 增加查看次數
      await axios.post(`/api/increment-view`, { tripId });

      // 如果您想保持在當前頁面但重新獲取數據
      fetchTripRankings(activeTab);
    } catch (err) {
      console.error('Error incrementing view count:', err);
    }
  };

  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const renderRankingTabs = () => (
    <div className="ranking-tabs">
      <button
        className={activeTab === 'view' ? 'active' : ''}
        onClick={() => setActiveTab('view')}
      >
        最多瀏覽
      </button>
      <button
        className={activeTab === 'area' ? 'active' : ''}
        onClick={() => setActiveTab('area')}
      >
        熱門地區
      </button>
      <button
        className={activeTab === 'date' ? 'active' : ''}
        onClick={() => setActiveTab('date')}
      >
        即將出發
      </button>
    </div>
  );

  const renderRankingList = () => {
    if (loading) return <div className="loading">加載中...</div>;
    if (error) return <div className="error">{error}</div>;
    if (trips.length === 0) return <div className="no-trips">沒有找到行程。</div>;

    return (
      <div className="ranking-list">
        {trips.map((trip, index) => (
          <div key={trip.trip_id} className="ranking-item">
            <div className="rank">{index + 1}</div>
            <div className="trip-info" onClick={() => handleViewTrip(trip.trip_id)}>
              <h3>{trip.title}</h3>
              <div className="trip-details">
                <span className="area">{trip.area}</span>
                <span className="date">{formatDate(trip.start_date)} - {formatDate(trip.end_date)}</span>
                <span className="views">{trip.view_count || 0} 瀏覽</span>
                {trip.total_participants && (
                  <span className="participants">{trip.total_participants} 參與者</span>
                )}
                {trip.tags && (
                  <div className="tags">
                    {trip.tags.split(',').map((tag, i) => (
                      <span key={i} className="tag">{tag.trim()}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="trip-ranking-container">
      <h2>行程排行榜</h2>
      {renderRankingTabs()}
      {renderRankingList()}
    </div>
  );
};

export default TripRanking;