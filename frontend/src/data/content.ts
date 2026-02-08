import thumbBreakingBad from "@/assets/thumb-breaking-bad.jpg";
import thumbNoir from "@/assets/thumb-noir.jpg";
import thumbScifi from "@/assets/thumb-scifi.jpg";
import thumbFantasy from "@/assets/thumb-fantasy.jpg";
import thumbHorror from "@/assets/thumb-horror.jpg";
import thumbAction from "@/assets/thumb-adventure.jpg"; // TODO: Replace with thumb-action.jpg when available
import thumbRomcom from "@/assets/thumb-romcom.jpg";
import thumbDocumentary from "@/assets/thumb-documentary.jpg";
import thumbAnime from "@/assets/thumb-anime.jpg";
import thumbCrime from "@/assets/thumb-crime.jpg";
import thumbAdventure from "@/assets/thumb-adventure.jpg";
import thumbStrangerThings from "@/assets/hero-stranger-things.png";
import thumbSquidGame from "@/assets/thumb-squid-game.jpg";

import videoStrangerThings from "@/assets/video/STS3E4.mp4";
import videoBreakingBad from "@/assets/video/BBS3E2.mp4";

import moviesData from "./movies.json";

/** Map of asset keys (from movies.json) to bundled image/video URLs */
const assetMap: Record<string, string> = {
  thumbBreakingBad,
  thumbNoir,
  thumbScifi,
  thumbFantasy,
  thumbHorror,
  thumbAction,
  thumbRomcom,
  thumbDocumentary,
  thumbAnime,
  thumbCrime,
  thumbAdventure,
  thumbStrangerThings,
  thumbSquidGame,
  videoStrangerThings,
  videoBreakingBad,
};

export interface ContentItem {
  id: string;
  title: string;
  video: string;
  image: string;
  ad_timing: number;
  ad_duration: number;
  match?: number;
  rating?: string;
  seasons?: number;
  description?: string;
  year?: number;
}

export interface ContentRow {
  title: string;
  items: ContentItem[];
}

export interface AppUser {
  id: number;
  key: "A" | "B";
  name: string;
  color: string;
  persona: string;
  vibe: string;
  focus: string;
  tags: string[];
}

export const users: AppUser[] = [
  {
    id: 1,
    key: "A",
    name: "User A",
    color: "hsl(356, 78%, 52%)",
    persona: "Deal-Seeker",
    vibe: "Comfort-first, deal-aware, cozy watch sessions.",
    focus: "Frozen pizza, cola, and quick delivery wins.",
    tags: ["Deal-Seeker", "Comfort Food"],
  },
  {
    id: 2,
    key: "B",
    name: "User B",
    color: "hsl(205, 88%, 55%)",
    persona: "Local Foodie",
    vibe: "Balanced choices, clean ingredients, mindful habits.",
    focus: "Sparkling beverages, protein-forward snacks.",
    tags: ["Local Foodie", "Premium"],
  },
];

/** Movie record from movies.json (synced from Snowflake via npm run movies:pull) */
interface MovieRecord {
  id: string;
  title: string;
  video_path: string;
  image_path: string;
  ad_timing: number;
  ad_duration: number;
  match?: number;
  rating?: string;
  seasons?: number;
  description?: string;
  year?: number;
}

/** Build content (allContent, contentRows, featuredContent) from a list of movie records. */
export function buildContentFromMovies(movies: MovieRecord[]): {
  allContent: ContentItem[];
  contentRows: ContentRow[];
  featuredContent: ContentItem;
} {
  const allContent: ContentItem[] = movies.map((m) => ({
    id: m.id,
    title: m.title,
    video: assetMap[m.video_path] ?? thumbStrangerThings,
    image: assetMap[m.image_path] ?? thumbStrangerThings,
    ad_timing: m.ad_timing,
    ad_duration: m.ad_duration,
    match: m.match,
    rating: m.rating,
    seasons: m.seasons,
    description: m.description,
    year: m.year,
  }));
  const contentRowConfig: { title: string; itemIds: string[] }[] = [
    { title: "Trending Now", itemIds: ["2", "3", "4", "5", "6"] },
    { title: "Popular on Netflix", itemIds: ["7", "8", "9", "10", "11", "12"] },
    { title: "Top 10 in Your Country", itemIds: ["2", "1", "5", "10", "11", "4"] },
    { title: "New Releases", itemIds: ["7", "9", "4", "11", "8", "3"] },
    { title: "My List", itemIds: ["1", "5", "8", "10", "2", "9"] },
  ];
  const byId = new Map(allContent.map((c) => [c.id, c]));
  const contentRows: ContentRow[] = contentRowConfig.map((row) => ({
    title: row.title,
    items: row.itemIds.map((id) => byId.get(id)).filter(Boolean) as ContentItem[],
  }));
  return { allContent, contentRows, featuredContent: allContent[0]! };
}

const staticContent = buildContentFromMovies(moviesData as MovieRecord[]);
const allContent = staticContent.allContent;
const contentRows = staticContent.contentRows;
const featuredContent = staticContent.featuredContent;

export { contentRows, featuredContent, allContent };
