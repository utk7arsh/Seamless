/**
 * Content ID → list of ad segments. Each segment has a storage path (video to play)
 * and start/end times in the main video; the timeline glows with the segment color.
 */
export interface AdSegment {
  /** Path to the ad video (e.g. /video/ad.mp4). */
  storagePath: string;
  /** Start time in seconds in the main video where this ad slot begins. */
  startTime: number;
  /** End time in seconds in the main video; after the ad we resume here. */
  endTime: number;
  /** Optional hex color for the timeline glow (e.g. "#f59e0b"). */
  color?: string;
}

export interface ContentAdSegmentsEntry {
  contentId: string;
  ads: AdSegment[];
}

import segmentsJson from "./contentAdSegments.json";

const segmentsByContentId = new Map<string, AdSegment[]>(
  (segmentsJson as ContentAdSegmentsEntry[]).map((entry) => [entry.contentId, entry.ads])
);

const DEFAULT_COLORS = ["#f59e0b", "#22c55e", "#3b82f6", "#a855f7", "#ec4899"];

/** Returns the list of ad segments for a content id, or empty array if none. */
export function getAdsForContent(contentId: string): AdSegment[] {
  const ads = segmentsByContentId.get(contentId) ?? [];
  return ads.map((ad, i) => ({
    ...ad,
    color: ad.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length],
  }));
}
