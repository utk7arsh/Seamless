# Thumbnail Storage Setup (Snowflake)

This guide shows how to store and serve thumbnail images using Snowflake.

## 1. Setup Snowflake Table

Run the DDL in Snowflake:

```bash
snowsql -f seamless_ads/thumbnail_storage.sql
```

Or manually execute `thumbnail_storage.sql` in Snowflake UI.

## 2. Configure Environment Variables

### Backend (Python)

Create `.env` or set environment variables:

```bash
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_ACCOUNT="abc12345.us-east-1"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_DATABASE="SEAMLESS_DB"
export SNOWFLAKE_SCHEMA="PUBLIC"
```

### Frontend API (Node.js)

Add to `frontend/.env.local`:

```env
SNOWFLAKE_ACCOUNT=abc12345.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=SEAMLESS_DB
SNOWFLAKE_SCHEMA=PUBLIC
```

## 3. Install Dependencies

### Python

```bash
pip install snowflake-connector-python
```

### Node.js (Frontend API)

```bash
cd frontend
npm install snowflake-sdk
```

## 4. Upload Thumbnails

### Batch Upload (Automatic - Recommended)

Simply run the script with no arguments to upload all thumbnails from `frontend/src/assets/`:

```bash
python seamless_ads/upload_thumbnail.py
```

The script will:
1. Scan `frontend/src/assets/` for all image files
2. Map filenames to content IDs automatically
3. Show a preview of what will be uploaded
4. Ask for confirmation
5. Upload all thumbnails in batch
6. Skip duplicates automatically
7. Show a summary report

**Example output:**

```
======================================================================
Seamless Ads - Batch Thumbnail Uploader
======================================================================

Thumbnails directory: /path/to/frontend/src/assets

Found 12 thumbnail(s):

  • hero-stranger-things.png    → stranger-things       (Stranger Things)
  • thumb-breaking-bad.jpg      → breaking-bad          (Breaking Bad)
  • thumb-adventure.jpg         → velocity              (Velocity)
  ...

──────────────────────────────────────────────────────────────────────
Upload 12 thumbnail(s) to Snowflake? [y/N]: y

Connecting to Snowflake...
✓ Connected

──────────────────────────────────────────────────────────────────────
Uploading thumbnails...

  Uploading hero-stranger-things.png (245,123 bytes)... ✓ Success (ID: abc-123)
  Uploading thumb-breaking-bad.jpg (198,456 bytes)... ✓ Success (ID: def-456)
  ...

======================================================================
Upload Summary:
  ✓ Uploaded:     12
  ⚠ Skipped:      0 (already exist)
  ✗ Failed:       0
  Total:          12
======================================================================
```

### Single File Upload (Manual)

For uploading individual files:

```bash
python seamless_ads/upload_thumbnail.py \
  path/to/image.jpg \
  "content-id" \
  "Content Title"
```

**Constraints:**
- Max file size: 2MB
- Supported formats: JPEG, PNG, WebP

## 5. Use in Frontend

### Import the component:

```tsx
import ThumbnailImage from '@/components/ThumbnailImage';

function MyComponent() {
  return (
    <ThumbnailImage 
      contentId="stranger-things"
      alt="Stranger Things"
      className="w-64 h-36 object-cover rounded"
      fallbackSrc="/placeholder.jpg"
    />
  );
}
```

### How it works:

1. Component calls `GET /api/thumbnail?contentId=stranger-things`
2. API route queries Snowflake (credentials NEVER exposed to frontend)
3. API converts BINARY → base64 and returns `{ image: "data:image/jpeg;base64,..." }`
4. Component renders the image in `<img>` tag

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ GET /api/thumbnail?contentId=...
       ▼
┌─────────────┐
│  Next.js    │  (Snowflake credentials)
│  API Route  │──────────────┐
└──────┬──────┘              │
       │                     ▼
       │              ┌─────────────┐
       │              │  Snowflake  │
       │              │   Database  │
       │              └─────────────┘
       │ Returns:
       │ { image: "data:image/jpeg;base64,..." }
       ▼
┌─────────────┐
│   <img>     │
│   tag       │
└─────────────┘
```

## Example: Full Workflow

```bash
# 1. Create table (run once)
snowsql -f seamless_ads/thumbnail_storage.sql

# 2. Upload ALL thumbnails automatically
python seamless_ads/upload_thumbnail.py
# (Press 'y' when prompted)

# 3. Start Next.js dev server
cd frontend
npm run dev

# 4. Use component in React
# <ThumbnailImage contentId="stranger-things" alt="Stranger Things" />
```

## Troubleshooting

### "File too large" error
- Resize images to <2MB before upload
- Use ImageMagick: `convert input.jpg -quality 85 -resize 1920x1080 output.jpg`

### "Thumbnail not found" (404)
- Check `content_id` matches exactly
- Query Snowflake: `SELECT * FROM thumbnail_images WHERE content_id = 'stranger-things';`

### Need to add a new thumbnail?
1. Add image file to `frontend/src/assets/` (name it like `thumb-my-show.jpg`)
2. Add mapping to `CONTENT_MAPPING` in `upload_thumbnail.py`:
   ```python
   "thumb-my-show": {"id": "my-show", "title": "My Show"},
   ```
3. Run: `python seamless_ads/upload_thumbnail.py`

### Re-upload all thumbnails
- The script automatically skips existing thumbnails
- To force re-upload, delete from Snowflake first:
  ```sql
  DELETE FROM thumbnail_images WHERE content_id = 'stranger-things';
  ```

### API route 500 error
- Check `frontend/.env.local` has all Snowflake credentials
- Verify Snowflake warehouse is running
- Check console logs: `npm run dev` shows detailed errors

### Slow queries
- Snowflake auto-clusters by `content_id` and `created_at`
- No manual indexing needed
- Queries should be <500ms

## Security Notes

- ✅ Snowflake credentials stored server-side only (`frontend/.env.local`)
- ✅ Never exposed to browser/frontend
- ✅ API route validates `contentId` parameter
- ⚠️ For production: Add authentication to `/api/thumbnail` endpoint
- ⚠️ For production: Use Snowflake OAuth instead of password auth

## Performance

- Small thumbnails (~100KB): ~200-300ms response time
- Large thumbnails (~2MB): ~500-800ms response time
- Consider adding Redis cache for frequently accessed thumbnails

## Cost Optimization

Snowflake charges for:
- **Storage**: ~$40/TB/month (tiny for images)
- **Compute**: Warehouse running time

Tips:
- Use smallest warehouse (X-Small) for API queries
- Auto-suspend warehouse after 1 minute idle
- Cache frequently accessed thumbnails in Redis/CDN
