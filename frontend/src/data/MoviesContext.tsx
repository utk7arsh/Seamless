import { createContext, useContext, useState, useEffect, useMemo, type ReactNode } from "react";
import {
  buildContentFromMovies,
  allContent as staticAllContent,
  contentRows as staticContentRows,
  featuredContent as staticFeaturedContent,
  type ContentItem,
  type ContentRow,
} from "./content";

type MoviesContextValue = {
  allContent: ContentItem[];
  contentRows: ContentRow[];
  featuredContent: ContentItem;
};

const defaultValue: MoviesContextValue = {
  allContent: staticAllContent,
  contentRows: staticContentRows,
  featuredContent: staticFeaturedContent,
};

const MoviesContext = createContext<MoviesContextValue>(defaultValue);

export function MoviesProvider({ children }: { children: ReactNode }) {
  const [content, setContent] = useState<MoviesContextValue>(defaultValue);

  useEffect(() => {
    fetch("/api/movies")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((movies: unknown) => {
        if (Array.isArray(movies) && movies.length > 0) {
          setContent(buildContentFromMovies(movies as Parameters<typeof buildContentFromMovies>[0]));
        }
      })
      .catch(() => {});
  }, []);

  const value = useMemo(() => content, [content]);

  return <MoviesContext.Provider value={value}>{children}</MoviesContext.Provider>;
}

export function useMovies(): MoviesContextValue {
  return useContext(MoviesContext);
}
