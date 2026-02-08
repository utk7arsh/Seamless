/**
 * User- and content-scoped ad segments. Each segment has a storage path (video to play)
 * and start/end times in the main video; the timeline glows with the segment color.
 * Ads are segregated by user: different users see different creatives for the same content.
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
  /** User id (matches AppUser.id from content.ts). */
  userId: number;
  contentId: string;
  ads: AdSegment[];
}

import segmentsJson from "./contentAdSegments.json";

const entries = segmentsJson as ContentAdSegmentsEntry[];
const segmentsByUserAndContent = new Map<string, AdSegment[]>(
  entries.map((e) => [`${e.userId}-${e.contentId}`, e.ads])
);

const DEFAULT_COLORS = ["#f59e0b", "#22c55e", "#3b82f6", "#a855f7", "#ec4899"];

/**
 * Returns ad segments for the given content and user. Different users get different ads
 * for the same content (user-based segregation). Returns an empty array if none are defined.
 */
export function getAdsForContent(contentId: string, userId: number): AdSegment[] {
  const key = `${userId}-${contentId}`;
  const ads = segmentsByUserAndContent.get(key) ?? [];
  return ads.map((ad, i) => ({
    ...ad,
    color: ad.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length],
  }));
}
