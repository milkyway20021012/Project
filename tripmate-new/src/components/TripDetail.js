// components/TripDetail.js
import React from 'react';
import './TripDetail.css';

const TripDetail = ({ trip, details, participants, onClose }) => {
  if (!trip) return null;

  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const formatTime = (timeString) => {
    return timeString.substring(0, 5); // 取出HH:MM部分
  };

  // 將標籤拆分為數組
  const tags = trip.tags ? trip.tags.split(',').map(tag => tag.trim()) : [];

  return (
    <div className="trip-detail-overlay" onClick={onClose}>
      <div className="trip-detail-container" onClick={e => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>&times;</button>

        <div className="trip-detail-header">
          <h2>{trip.title}</h2>
          <div className="trip-meta">
            <span className="trip-creator">由 {trip.creator_name} 創建</span>
            <span className="trip-views">👁️ {trip.view_count || 0} 次瀏覽</span>
          </div>
        </div>

        <div className="trip-detail-content">
          <div className="trip-info-panel">
            <div className="trip-info-section">
              <h3>行程資訊</h3>
              <div className="trip-info-grid">
                <div className="info-item">
                  <label>地區</label>
                  <span>{trip.area}</span>
                </div>
                <div className="info-item">
                  <label>結束日期</label>
                  <span>{formatDate(trip.end_date)}</span>
                </div>
                <div className="info-item">
                  <label>預算</label>
                  <span>{trip.budget ? `${trip.budget}` : '未設定'}</span>
                </div>
              </div>
            </div>

            {trip.description && (
              <div className="trip-info-section">
                <h3>行程介紹</h3>
                <p className="trip-description">{trip.description}</p>
              </div>
            )}

            {tags.length > 0 && (
              <div className="trip-info-section">
                <h3>標籤</h3>
                <div className="trip-tags">
                  {tags.map((tag, index) => (
                    <span key={index} className="trip-tag">{tag}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="trip-schedule">
            <h3>行程安排</h3>
            {details.length > 0 ? (
              <div className="schedule-timeline">
                {details.map((detail, index) => (
                  <div key={detail.detail_id} className="schedule-item">
                    <div className="schedule-time">
                      <div className="schedule-date">{formatDate(detail.date)}</div>
                      <div className="schedule-hours">{formatTime(detail.start_time)} - {formatTime(detail.end_time)}</div>
                    </div>
                    <div className="schedule-dot"></div>
                    <div className="schedule-content">
                      <h4>{detail.location}</h4>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-details">尚未安排行程細節</p>
            )}
          </div>

          <div className="trip-participants">
            <h3>參與者 ({participants.length})</h3>
            <div className="participants-list">
              {participants.map((participant) => (
                <div key={participant.participant_id} className={`participant-item ${participant.status}`}>
                  <span className="participant-name">{participant.username}</span>
                  <span className="participant-status">
                    {participant.status === 'accepted' ? '已接受' :
                      participant.status === 'invited' ? '已邀請' : '已拒絕'}
                  </span>
                </div>
              ))}
              {participants.length === 0 && (
                <p className="no-participants">尚無參與者</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TripDetail;