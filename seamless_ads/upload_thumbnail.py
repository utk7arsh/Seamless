"""
Batch upload all thumbnail images to Snowflake
Scans frontend/src/assets/ for thumbnails and uploads them automatically
Usage: python upload_thumbnail.py
"""

import os
import sys
from pathlib import Path
import snowflake.connector
from typing import Optional
import re

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] Loaded environment variables from {env_path}")
except ImportError:
    pass  # python-dotenv not installed, use system env vars

# Snowflake connection config (set via environment variables)
SNOWFLAKE_CONFIG = {
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    'database': os.getenv('SNOWFLAKE_DATABASE', 'SEAMLESS_DB'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC'),
}

def validate_snowflake_config():
    """
    Validate that required Snowflake environment variables are set
    """
    required = ['user', 'password', 'account']
    missing = [key.upper() for key in required if not SNOWFLAKE_CONFIG.get(key)]
    
    if missing:
        print("\n" + "=" * 70)
        print("[ERROR] Missing required Snowflake environment variables:")
        for var in missing:
            print(f"  - SNOWFLAKE_{var}")
        print("=" * 70)
        
        env_file = Path(__file__).parent / '.env'
        env_example = Path(__file__).parent / '.env.example'
        
        print("\nOPTION 1: Create a .env file (Recommended)")
        print(f"   Copy {env_example.name} to .env and fill in your credentials:")
        if env_example.exists():
            print(f"   $ copy {env_example.name} .env  (Windows)")
            print(f"   $ cp {env_example.name} .env    (Linux/Mac)")
        print(f"   Then edit {env_file.name} with your Snowflake credentials")
        print("   Install python-dotenv: pip install python-dotenv")
        
        print("\nOPTION 2: Set environment variables")
        print("   Windows (PowerShell):")
        for var in missing:
            print(f"     $env:SNOWFLAKE_{var}=\"your_value\"")
        print("\n   Windows (CMD):")
        for var in missing:
            print(f"     set SNOWFLAKE_{var}=your_value")
        print("\n   Linux/Mac:")
        for var in missing:
            print(f"     export SNOWFLAKE_{var}=\"your_value\"")
        
        print("\n" + "=" * 70)
        sys.exit(1)

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# Directory containing thumbnails
THUMBNAILS_DIR = Path(__file__).parent.parent / "frontend" / "src" / "assets"

# Mapping from filename patterns to content metadata
CONTENT_MAPPING = {
    "hero-stranger-things": {"id": "stranger-things", "title": "Stranger Things"},
    "thumb-breaking-bad": {"id": "breaking-bad", "title": "Breaking Bad"},
    "thumb-noir": {"id": "dark-city", "title": "Dark City"},
    "thumb-scifi": {"id": "beyond-earth", "title": "Beyond Earth"},
    "thumb-fantasy": {"id": "dragons-reign", "title": "Dragon's Reign"},
    "thumb-horror": {"id": "the-haunting", "title": "The Haunting"},
    "thumb-adventure": {"id": "velocity", "title": "Velocity"},
    "thumb-action": {"id": "velocity", "title": "Velocity"},
    "thumb-romcom": {"id": "paris-connection", "title": "Paris Connection"},
    "thumb-documentary": {"id": "deep-blue", "title": "Deep Blue"},
    "thumb-anime": {"id": "neon-district", "title": "Neon District"},
    "thumb-crime": {"id": "the-syndicate", "title": "The Syndicate"},
    "thumb-squid-game": {"id": "squid-game", "title": "Squid Game"},
}

def validate_image(file_path: str) -> tuple[bytes, str, int]:
    """
    Validate image file and return (binary_data, content_type, file_size)
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {file_path}")
    
    # Check file size
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE})")
    
    # Determine content type from extension
    ext = path.suffix.lower()
    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
    }
    
    content_type = content_type_map.get(ext)
    if not content_type:
        raise ValueError(f"Unsupported image format: {ext}")
    
    # Read binary data
    with open(file_path, 'rb') as f:
        binary_data = f.read()
    
    return binary_data, content_type, file_size

def get_content_info(filename: str) -> Optional[dict]:
    """
    Extract content_id and content_title from filename using mapping
    Returns dict with 'id' and 'title' keys, or None if not found
    """
    # Remove extension
    name_without_ext = Path(filename).stem
    
    # Try exact match first
    if name_without_ext in CONTENT_MAPPING:
        return CONTENT_MAPPING[name_without_ext]
    
    # Try partial match
    for pattern, info in CONTENT_MAPPING.items():
        if pattern in name_without_ext.lower():
            return info
    
    # Fallback: derive from filename
    # Convert "thumb-breaking-bad" -> "breaking-bad", "Breaking Bad"
    content_id = name_without_ext.replace("thumb-", "").replace("hero-", "")
    content_title = content_id.replace("-", " ").replace("_", " ").title()
    
    return {"id": content_id, "title": content_title}

def upload_thumbnail(
    conn,
    cursor,
    image_path: str,
    content_id: str,
    content_title: str,
    thumbnail_id: Optional[str] = None
) -> str:
    """
    Upload thumbnail to Snowflake using existing connection
    Returns the thumbnail_id
    """
    # Validate image
    binary_data, content_type, file_size = validate_image(image_path)
    filename = Path(image_path).name
    
    print(f"  Uploading {filename} ({file_size:,} bytes)...", end=" ")
    
    try:
        # Check if already exists
        cursor.execute("""
            SELECT thumbnail_id FROM thumbnail_images 
            WHERE content_id = %(content_id)s
        """, {'content_id': content_id})
        
        existing = cursor.fetchone()
        if existing:
            print(f"[SKIP] Already exists (ID: {existing[0]})")
            return existing[0]
        
        # Insert thumbnail
        insert_sql = """
        INSERT INTO thumbnail_images (
            thumbnail_id,
            image_data,
            filename,
            content_type,
            file_size_bytes,
            content_id,
            content_title
        ) VALUES (
            COALESCE(%(thumbnail_id)s, UUID_STRING()),
            %(image_data)s,
            %(filename)s,
            %(content_type)s,
            %(file_size_bytes)s,
            %(content_id)s,
            %(content_title)s
        )
        """
        
        cursor.execute(insert_sql, {
            'thumbnail_id': thumbnail_id,
            'image_data': binary_data,
            'filename': filename,
            'content_type': content_type,
            'file_size_bytes': file_size,
            'content_id': content_id,
            'content_title': content_title,
        })
        
        # Get the inserted thumbnail_id
        cursor.execute("""
            SELECT thumbnail_id 
            FROM thumbnail_images 
            WHERE content_id = %(content_id)s 
            ORDER BY created_at DESC 
            LIMIT 1
        """, {'content_id': content_id})
        
        result = cursor.fetchone()
        inserted_id = result[0] if result else "unknown"
        
        print(f"[OK] Success (ID: {inserted_id})")
        return inserted_id
        
    except Exception as e:
        print(f"[FAIL] {e}")
        raise

def find_all_thumbnails() -> list[Path]:
    """
    Find all thumbnail images in the assets directory
    """
    if not THUMBNAILS_DIR.exists():
        print(f"[ERROR] Thumbnails directory not found: {THUMBNAILS_DIR}")
        return []
    
    extensions = ['.jpg', '.jpeg', '.png', '.webp']
    thumbnails = []
    
    for ext in extensions:
        thumbnails.extend(THUMBNAILS_DIR.glob(f"*{ext}"))
        # On Windows, glob is case-insensitive, so skip uppercase
        # On Unix, add uppercase variant
        if os.name != 'nt':
            thumbnails.extend(THUMBNAILS_DIR.glob(f"*{ext.upper()}"))
    
    # Remove duplicates (can happen on some systems)
    return sorted(list(set(thumbnails)))

def upload_all_thumbnails():
    """
    Batch upload all thumbnails from the assets directory
    """
    print("=" * 70)
    print("Seamless Ads - Batch Thumbnail Uploader")
    print("=" * 70)
    
    # Validate config first
    validate_snowflake_config()
    
    print(f"\nThumbnails directory: {THUMBNAILS_DIR}")
    
    # Find all thumbnails
    thumbnails = find_all_thumbnails()
    
    if not thumbnails:
        print("\n[ERROR] No thumbnails found!")
        return
    
    print(f"\nFound {len(thumbnails)} thumbnail(s):\n")
    
    # Preview what will be uploaded
    upload_plan = []
    for thumb_path in thumbnails:
        content_info = get_content_info(thumb_path.name)
        if content_info:
            upload_plan.append({
                'path': thumb_path,
                'content_id': content_info['id'],
                'content_title': content_info['title'],
            })
            print(f"  - {thumb_path.name:30s} -> {content_info['id']:20s} ({content_info['title']})")
        else:
            print(f"  [SKIP] {thumb_path.name} (no mapping found)")
    
    if not upload_plan:
        print("\n[ERROR] No valid thumbnails to upload!")
        return
    
    # Confirm upload
    print(f"\n{'-' * 70}")
    response = input(f"Upload {len(upload_plan)} thumbnail(s) to Snowflake? [y/N]: ")
    if response.lower() not in ['y', 'yes']:
        print("Cancelled.")
        return
    
    # Connect to Snowflake once
    print("\nConnecting to Snowflake...")
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        cursor = conn.cursor()
        print("[OK] Connected\n")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return
    
    # Upload all thumbnails
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    print(f"{'-' * 70}")
    print("Uploading thumbnails...\n")
    
    for item in upload_plan:
        try:
            result = upload_thumbnail(
                conn, 
                cursor,
                str(item['path']),
                item['content_id'],
                item['content_title']
            )
            if "Already exists" in str(result):
                skip_count += 1
            else:
                success_count += 1
                conn.commit()
        except Exception as e:
            fail_count += 1
            print(f"  Error uploading {item['path'].name}: {e}")
    
    # Close connection
    cursor.close()
    conn.close()
    
    # Summary
    print(f"\n{'=' * 70}")
    print("Upload Summary:")
    print(f"  [OK]   Uploaded:  {success_count}")
    print(f"  [SKIP] Skipped:   {skip_count} (already exist)")
    print(f"  [FAIL] Failed:    {fail_count}")
    print(f"  Total:            {len(upload_plan)}")
    print("=" * 70)

def main():
    # Check if running in batch mode (no arguments) or single file mode
    if len(sys.argv) == 1:
        # Batch mode - upload all thumbnails
        try:
            upload_all_thumbnails()
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            sys.exit(1)
    else:
        # Single file mode (legacy support)
        if len(sys.argv) < 4:
            print("Usage:")
            print("  Batch mode:  python upload_thumbnail.py")
            print("  Single file: python upload_thumbnail.py <image_path> <content_id> <content_title>")
            sys.exit(1)
        
        # Validate config first
        validate_snowflake_config()
        
        image_path = sys.argv[1]
        content_id = sys.argv[2]
        content_title = sys.argv[3]
        
        try:
            # Connect to Snowflake
            conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
            cursor = conn.cursor()
            
            thumbnail_id = upload_thumbnail(conn, cursor, image_path, content_id, content_title)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            print(f"\nThumbnail ID: {thumbnail_id}")
            print(f"Content ID: {content_id}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
