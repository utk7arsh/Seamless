import thumbStrangerThings from "@/assets/hero-stranger-things.png";
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

export interface ContentItem {
  id: string;
  title: string;
  image: string;
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
    persona: "Late-Night Snacker",
    vibe: "Comfort-first, deal-aware, cozy watch sessions.",
    focus: "Frozen pizza, cola, and quick delivery wins.",
    tags: ["Late Night", "Deal-Seeker", "Comfort Food"],
  },
  {
    id: 2,
    key: "B",
    name: "User B",
    color: "hsl(205, 88%, 55%)",
    persona: "Wellness Optimizer",
    vibe: "Balanced choices, clean ingredients, mindful habits.",
    focus: "Sparkling beverages, protein-forward snacks.",
    tags: ["Balanced", "Premium", "Pickup-Friendly"],
  },
];

const allContent: ContentItem[] = [
  { id: "1", title: "Stranger Things", image: thumbStrangerThings, match: 98, rating: "16+", seasons: 4, description: "When a young boy vanishes, a small town uncovers a mystery involving secret experiments and the supernatural.", year: 2016 },
  { id: "2", title: "Breaking Bad", image: thumbBreakingBad, match: 97, rating: "18+", seasons: 5, description: "A chemistry teacher diagnosed with cancer teams up with a former student to manufacture crystal meth.", year: 2008 },
  { id: "3", title: "Dark City", image: thumbNoir, match: 92, rating: "16+", seasons: 3, description: "A detective navigates the shadowy underworld of a city consumed by corruption and secrets.", year: 2022 },
  { id: "4", title: "Beyond Earth", image: thumbScifi, match: 89, rating: "13+", seasons: 2, description: "An astronaut embarks on a perilous mission to save humanity from extinction.", year: 2023 },
  { id: "5", title: "Dragon's Reign", image: thumbFantasy, match: 95, rating: "16+", seasons: 4, description: "Kingdoms clash as ancient dragons awaken from their centuries-long slumber.", year: 2020 },
  { id: "6", title: "The Haunting", image: thumbHorror, match: 87, rating: "18+", seasons: 2, description: "A family moves into a house with a dark past, unleashing unspeakable horrors.", year: 2021 },
  { id: "7", title: "Velocity", image: thumbAction, match: 90, rating: "16+", seasons: 1, description: "An elite driver is drawn into an underground racing syndicate with deadly stakes.", year: 2024 },
  { id: "8", title: "Paris Connection", image: thumbRomcom, match: 85, rating: "13+", seasons: 3, description: "Two strangers keep running into each other across the romantic streets of Paris.", year: 2022 },
  { id: "9", title: "Deep Blue", image: thumbDocumentary, match: 93, rating: "PG", seasons: 1, description: "Explore the mysterious depths of Earth's oceans and the incredible creatures within.", year: 2023 },
  { id: "10", title: "Neon District", image: thumbAnime, match: 91, rating: "16+", seasons: 2, description: "In a cyberpunk future, a hacker uncovers a conspiracy that threatens all of society.", year: 2024 },
  { id: "11", title: "The Syndicate", image: thumbCrime, match: 88, rating: "18+", seasons: 3, description: "An undercover agent infiltrates one of the world's most dangerous criminal organizations.", year: 2021 },
  { id: "12", title: "Summit", image: thumbAdventure, match: 94, rating: "13+", seasons: 1, description: "A mountaineer attempts the impossible: summiting the world's most treacherous peaks solo.", year: 2023 },
];

export const contentRows: ContentRow[] = [
  {
    title: "Trending Now",
    items: [allContent[1], allContent[2], allContent[3], allContent[4], allContent[5]],
  },
  {
    title: "Popular on Netflix",
    items: [allContent[6], allContent[7], allContent[8], allContent[9], allContent[10], allContent[11]],
  },
  {
    title: "Top 10 in Your Country",
    items: [allContent[1], allContent[0], allContent[4], allContent[9], allContent[11], allContent[3]],
  },
  {
    title: "New Releases",
    items: [allContent[6], allContent[9], allContent[3], allContent[11], allContent[8], allContent[2]],
  },
  {
    title: "My List",
    items: [allContent[0], allContent[4], allContent[7], allContent[10], allContent[1], allContent[8]],
  },
];

export const featuredContent = allContent[0];
export { allContent };
