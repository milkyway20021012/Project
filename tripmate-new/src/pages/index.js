// pages/index.js - 完整的主頁面
import { useState } from 'react';
import TripList from '../components/TripList';
import TripRanking from '../components/TripRanking';

export default function Home() {
  const [activeTab, setActiveTab] = useState('list');

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* 導航標籤 */}
      <nav style={{
        backgroundColor: 'white',
        padding: '1rem 0',
        borderBottom: '1px solid #e0e0e0',
        marginBottom: '2rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 20px',
          display: 'flex',
          gap: '2rem',
          alignItems: 'center'
        }}>
          <h1 style={{
            margin: 0,
            color: '#2c3e50',
            fontSize: '28px',
            fontWeight: 'bold'
          }}>
            🧳 TripMate
          </h1>

          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              onClick={() => setActiveTab('list')}
              style={{
                padding: '0.8rem 1.5rem',
                backgroundColor: activeTab === 'list' ? '#3498db' : 'white',
                color: activeTab === 'list' ? 'white' : '#333',
                border: '2px solid #3498db',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 'bold',
                transition: 'all 0.3s ease',
                boxShadow: activeTab === 'list' ? '0 2px 8px rgba(52, 152, 219, 0.3)' : 'none'
              }}
              onMouseOver={(e) => {
                if (activeTab !== 'list') {
                  e.target.style.backgroundColor = '#f8f9fa';
                }
              }}
              onMouseOut={(e) => {
                if (activeTab !== 'list') {
                  e.target.style.backgroundColor = 'white';
                }
              }}
            >
              📋 行程列表
            </button>

            <button
              onClick={() => setActiveTab('ranking')}
              style={{
                padding: '0.8rem 1.5rem',
                backgroundColor: activeTab === 'ranking' ? '#3498db' : 'white',
                color: activeTab === 'ranking' ? 'white' : '#333',
                border: '2px solid #3498db',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 'bold',
                transition: 'all 0.3s ease',
                boxShadow: activeTab === 'ranking' ? '0 2px 8px rgba(52, 152, 219, 0.3)' : 'none'
              }}
              onMouseOver={(e) => {
                if (activeTab !== 'ranking') {
                  e.target.style.backgroundColor = '#f8f9fa';
                }
              }}
              onMouseOut={(e) => {
                if (activeTab !== 'ranking') {
                  e.target.style.backgroundColor = 'white';
                }
              }}
            >
              🏆 排行榜
            </button>
          </div>

          <div style={{ marginLeft: 'auto', display: 'flex', gap: '1rem' }}>
            <a
              href="/api/simple-test"
              target="_blank"
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#27ae60',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                transition: 'all 0.3s ease'
              }}
              onMouseOver={(e) => {
                e.target.style.backgroundColor = '#229954';
              }}
              onMouseOut={(e) => {
                e.target.style.backgroundColor = '#27ae60';
              }}
            >
              🔧 系統狀態
            </a>
          </div>
        </div>
      </nav>

      {/* 主要內容 */}
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 20px' }}>
        {activeTab === 'list' && <TripList />}
        {activeTab === 'ranking' && <TripRanking />}
      </main>

      {/* 頁腳 */}
      <footer style={{
        backgroundColor: '#2c3e50',
        color: 'white',
        textAlign: 'center',
        padding: '2rem 0',
        marginTop: '4rem'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 20px' }}>
          <p style={{ margin: 0, fontSize: '16px' }}>
            © 2024 TripMate - 讓旅行更美好 ✈️
          </p>
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '14px', opacity: 0.8 }}>
            探索世界，分享回憶
          </p>
        </div>
      </footer>
    </div>
  );
}