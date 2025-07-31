#!/usr/bin/env python3
"""
測試 MySQL 連接器導入
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mysql_import():
    """測試 MySQL 連接器導入"""
    try:
        import mysql.connector
        logger.info("✅ MySQL connector imported successfully")
        logger.info(f"MySQL connector version: {mysql.connector.__version__}")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import MySQL connector: {e}")
        return False

def test_database_utils():
    """測試 database_utils 模組"""
    try:
        from api.database_utils import get_database_connection, MYSQL_AVAILABLE
        logger.info("✅ database_utils imported successfully")
        logger.info(f"MySQL available: {MYSQL_AVAILABLE}")
        
        # 測試連接（不會實際連接，只是測試函數）
        connection = get_database_connection()
        if connection is None:
            logger.info("⚠️  Database connection returned None (expected if no DB configured)")
        else:
            logger.info("✅ Database connection successful")
            connection.close()
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to test database_utils: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== MySQL Import Test ===")
    
    mysql_ok = test_mysql_import()
    utils_ok = test_database_utils()
    
    if mysql_ok and utils_ok:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Some tests failed!")
        sys.exit(1)
