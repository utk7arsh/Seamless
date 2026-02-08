-- Snowflake Table for Storing Thumbnail Images (Max ~2MB each)
-- No traditional indexes - Snowflake uses automatic micro-partitions

CREATE OR REPLACE TABLE thumbnail_images (
    thumbnail_id VARCHAR(36) PRIMARY KEY DEFAULT UUID_STRING(),
    
    -- Binary image data (max ~2MB - enforced in application layer)
    image_data BINARY NOT NULL,
    
    -- Metadata
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL, -- 'image/jpeg', 'image/png', 'image/webp'
    file_size_bytes INTEGER NOT NULL,
    content_id VARCHAR(100), -- Links to video/content
    content_title VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (content_id, created_at); -- Snowflake clustering for query performance

-- Example query to retrieve thumbnail:
-- SELECT thumbnail_id, filename, image_data, content_type, file_size_bytes
-- FROM thumbnail_images
-- WHERE content_id = 'stranger-things';
