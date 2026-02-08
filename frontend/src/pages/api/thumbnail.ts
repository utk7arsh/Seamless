/**
 * API Route: GET /api/thumbnail?contentId=<id>
 * Fetches thumbnail from Snowflake and returns as base64 data URL
 * 
 * Setup: Install snowflake-sdk
 * npm install snowflake-sdk
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import snowflake from 'snowflake-sdk';

// Snowflake connection config (NEVER expose to frontend)
const snowflakeConfig = {
  account: process.env.SNOWFLAKE_ACCOUNT!,
  username: process.env.SNOWFLAKE_USER!,
  password: process.env.SNOWFLAKE_PASSWORD!,
  warehouse: process.env.SNOWFLAKE_WAREHOUSE || 'COMPUTE_WH',
  database: process.env.SNOWFLAKE_DATABASE || 'SEAMLESS_DB',
  schema: process.env.SNOWFLAKE_SCHEMA || 'PUBLIC',
};

interface ThumbnailResponse {
  image?: string; // data:image/...;base64,...
  error?: string;
  contentId?: string;
  filename?: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ThumbnailResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { contentId } = req.query;

  if (!contentId || typeof contentId !== 'string') {
    return res.status(400).json({ error: 'Missing contentId parameter' });
  }

  try {
    // Connect to Snowflake
    const connection = snowflake.createConnection(snowflakeConfig);

    await new Promise<void>((resolve, reject) => {
      connection.connect((err, conn) => {
        if (err) reject(err);
        else resolve();
      });
    });

    // Query thumbnail
    const result = await new Promise<any>((resolve, reject) => {
      connection.execute({
        sqlText: `
          SELECT 
            image_data,
            content_type,
            filename,
            file_size_bytes
          FROM thumbnail_images
          WHERE content_id = ?
          ORDER BY created_at DESC
          LIMIT 1
        `,
        binds: [contentId],
        complete: (err, stmt, rows) => {
          if (err) reject(err);
          else resolve(rows);
        },
      });
    });

    // Close connection
    connection.destroy();

    if (!result || result.length === 0) {
      return res.status(404).json({ 
        error: 'Thumbnail not found',
        contentId 
      });
    }

    const row = result[0];
    const imageBuffer = Buffer.from(row.IMAGE_DATA, 'hex');
    const base64Image = imageBuffer.toString('base64');
    const contentType = row.CONTENT_TYPE;
    const dataUrl = `data:${contentType};base64,${base64Image}`;

    return res.status(200).json({
      image: dataUrl,
      contentId,
      filename: row.FILENAME,
    });

  } catch (error) {
    console.error('Snowflake error:', error);
    return res.status(500).json({ 
      error: 'Failed to fetch thumbnail',
      contentId 
    });
  }
}
