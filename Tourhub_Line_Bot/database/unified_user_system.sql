-- 統一用戶管理系統資料庫表

-- 1. 統一用戶表
CREATE TABLE IF NOT EXISTS unified_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    line_user_id VARCHAR(100) UNIQUE NOT NULL COMMENT 'LINE用戶ID',
    display_name VARCHAR(100) COMMENT 'LINE顯示名稱',
    picture_url TEXT COMMENT 'LINE頭像URL',
    email VARCHAR(255) COMMENT '用戶郵箱',
    phone VARCHAR(20) COMMENT '用戶電話',
    unified_token VARCHAR(255) UNIQUE COMMENT '統一認證Token',
    is_verified BOOLEAN DEFAULT FALSE COMMENT '是否已驗證',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL COMMENT '最後登入時間',
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active' COMMENT '用戶狀態',
    
    INDEX idx_line_user_id (line_user_id),
    INDEX idx_unified_token (unified_token),
    INDEX idx_status (status)
) COMMENT='統一用戶管理表';

-- 2. 網站模組配置表
CREATE TABLE IF NOT EXISTS website_modules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module_name VARCHAR(50) UNIQUE NOT NULL COMMENT '模組名稱',
    module_display_name VARCHAR(100) NOT NULL COMMENT '模組顯示名稱',
    base_url VARCHAR(255) NOT NULL COMMENT '模組基礎URL',
    api_key VARCHAR(255) COMMENT '模組API密鑰',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否啟用',
    description TEXT COMMENT '模組描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_module_name (module_name),
    INDEX idx_is_active (is_active)
) COMMENT='網站模組配置表';

-- 3. 用戶網站綁定表
CREATE TABLE IF NOT EXISTS user_website_bindings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unified_user_id INT NOT NULL COMMENT '統一用戶ID',
    module_id INT NOT NULL COMMENT '網站模組ID',
    external_user_id VARCHAR(100) COMMENT '外部網站用戶ID',
    access_token TEXT COMMENT '訪問Token',
    refresh_token TEXT COMMENT '刷新Token',
    token_expires_at TIMESTAMP NULL COMMENT 'Token過期時間',
    binding_data JSON COMMENT '綁定相關數據',
    is_active BOOLEAN DEFAULT TRUE COMMENT '綁定是否有效',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (unified_user_id) REFERENCES unified_users(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES website_modules(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_module (unified_user_id, module_id),
    INDEX idx_unified_user_id (unified_user_id),
    INDEX idx_module_id (module_id),
    INDEX idx_is_active (is_active)
) COMMENT='用戶網站綁定關係表';

-- 4. 用戶操作日誌表
CREATE TABLE IF NOT EXISTS user_operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unified_user_id INT NOT NULL COMMENT '統一用戶ID',
    module_id INT COMMENT '操作的網站模組ID',
    operation_type VARCHAR(50) NOT NULL COMMENT '操作類型',
    operation_data JSON COMMENT '操作數據',
    result_status ENUM('success', 'failed', 'pending') DEFAULT 'pending' COMMENT '操作結果',
    error_message TEXT COMMENT '錯誤訊息',
    ip_address VARCHAR(45) COMMENT '操作IP',
    user_agent TEXT COMMENT '用戶代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (unified_user_id) REFERENCES unified_users(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES website_modules(id) ON DELETE SET NULL,
    INDEX idx_unified_user_id (unified_user_id),
    INDEX idx_module_id (module_id),
    INDEX idx_operation_type (operation_type),
    INDEX idx_created_at (created_at)
) COMMENT='用戶操作日誌表';

-- 5. 系統配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL COMMENT '配置鍵',
    config_value TEXT COMMENT '配置值',
    config_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string' COMMENT '配置類型',
    description TEXT COMMENT '配置描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否啟用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_config_key (config_key),
    INDEX idx_is_active (is_active)
) COMMENT='系統配置表';

-- 插入預設的網站模組
INSERT INTO website_modules (module_name, module_display_name, base_url, description) VALUES
('tourhub_leaderboard', 'TourHub排行榜', 'https://tourhubashy.vercel.app', 'TourHub旅遊排行榜'),
('trip_management', '行程管理', 'https://tripfrontend.vercel.app/linetrip', 'LINE行程管理系統'),
('tour_clock', '集合管理', 'https://tourclock-dvf2.vercel.app', 'TourClock集合時間管理'),
('locker_finder', '置物櫃查找', 'https://tripfrontend.vercel.app/linelocker', '置物櫃位置查找服務'),
('bill_split', '分帳系統', 'https://split-front-pearl.vercel.app', '旅遊分帳管理')
ON DUPLICATE KEY UPDATE
    module_display_name = VALUES(module_display_name),
    base_url = VALUES(base_url),
    description = VALUES(description);

-- 插入系統配置
INSERT INTO system_configs (config_key, config_value, config_type, description) VALUES
('line_login_enabled', 'true', 'boolean', '是否啟用LINE Login'),
('unified_token_expire_days', '30', 'number', '統一Token過期天數'),
('max_website_bindings', '10', 'number', '用戶最大網站綁定數量'),
('auto_refresh_tokens', 'true', 'boolean', '是否自動刷新Token')
ON DUPLICATE KEY UPDATE 
    config_value = VALUES(config_value),
    description = VALUES(description);
