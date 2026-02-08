/**
 * React component to fetch and display thumbnails from Snowflake via API
 * Usage: <ThumbnailImage contentId="stranger-things" alt="Stranger Things" />
 */

import { useState, useEffect } from 'react';

interface ThumbnailImageProps {
  contentId: string;
  alt?: string;
  className?: string;
  fallbackSrc?: string;
}

interface ThumbnailData {
  image?: string;
  error?: string;
  filename?: string;
}

export default function ThumbnailImage({ 
  contentId, 
  alt = '', 
  className = '',
  fallbackSrc = '/placeholder.jpg'
}: ThumbnailImageProps) {
  const [imageData, setImageData] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchThumbnail = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/thumbnail?contentId=${encodeURIComponent(contentId)}`);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data: ThumbnailData = await response.json();

        if (data.error) {
          throw new Error(data.error);
        }

        if (data.image) {
          setImageData(data.image);
        } else {
          throw new Error('No image data returned');
        }

      } catch (err) {
        console.error('Failed to load thumbnail:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setImageData(fallbackSrc); // Use fallback
      } finally {
        setLoading(false);
      }
    };

    fetchThumbnail();
  }, [contentId, fallbackSrc]);

  if (loading) {
    return (
      <div className={`bg-gray-800 animate-pulse ${className}`}>
        <span className="sr-only">Loading thumbnail...</span>
      </div>
    );
  }

  if (error && !imageData) {
    return (
      <div className={`bg-gray-800 flex items-center justify-center ${className}`}>
        <span className="text-gray-500 text-sm">Failed to load</span>
      </div>
    );
  }

  return (
    <img 
      src={imageData || fallbackSrc} 
      alt={alt}
      className={className}
      loading="lazy"
    />
  );
}
