"""
Create the thumbnail_images table in Snowflake
Run this once before uploading thumbnails
Usage: python create_table.py
"""

import os
import sys
from pathlib import Path
import snowflake.connector

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] Loaded environment variables from {env_path}")
except ImportError:
    pass

# Snowflake connection config
SNOWFLAKE_CONFIG = {
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    'database': os.getenv('SNOWFLAKE_DATABASE', 'SEAMLESS_DB'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC'),
}

# DDL for creating the table
CREATE_TABLE_SQL = """
CREATE OR REPLACE TABLE thumbnail_images (
    thumbnail_id VARCHAR(36) PRIMARY KEY DEFAULT UUID_STRING(),
    
    -- Binary image data (max ~2MB)
    image_data BINARY NOT NULL,
    
    -- Metadata
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    content_id VARCHAR(100),
    content_title VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (content_id, created_at);
"""

def validate_config():
    """Validate required environment variables"""
    required = ['user', 'password', 'account']
    missing = [key.upper() for key in required if not SNOWFLAKE_CONFIG.get(key)]
    
    if missing:
        print("\n[ERROR] Missing required Snowflake environment variables:")
        for var in missing:
            print(f"  - SNOWFLAKE_{var}")
        print("\nCheck your .env file in seamless_ads/")
        sys.exit(1)

def create_table():
    """Create the thumbnail_images table in Snowflake"""
    print("=" * 70)
    print("Create Thumbnail Images Table in Snowflake")
    print("=" * 70)
    
    validate_config()
    
    print(f"\nDatabase: {SNOWFLAKE_CONFIG['database']}")
    print(f"Schema:   {SNOWFLAKE_CONFIG['schema']}")
    print(f"Table:    THUMBNAIL_IMAGES")
    
    print("\nConnecting to Snowflake...")
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        cursor = conn.cursor()
        print("[OK] Connected")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)
    
    print("\nCreating table...")
    try:
        cursor.execute(CREATE_TABLE_SQL)
        print("[OK] Table created successfully!")
        
        # Verify the table exists
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = '{SNOWFLAKE_CONFIG['schema']}'
            AND table_name = 'THUMBNAIL_IMAGES'
        """)
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            print("[OK] Table verified in database")
        
        conn.commit()
        
    except Exception as e:
        print(f"[ERROR] Failed to create table: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
    
    print("\n" + "=" * 70)
    print("SUCCESS! You can now upload thumbnails:")
    print("  python seamless_ads/upload_thumbnail.py")
    print("=" * 70)

if __name__ == '__main__':
    try:
        create_table()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
