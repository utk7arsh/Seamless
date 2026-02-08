import { Play, Info } from "lucide-react";
import heroImage from "@/assets/hero-stranger-things.png";
import { useMovies } from "@/data/MoviesContext";

interface HeroBannerProps {
  onPlay: (id: string) => void;
}

const HeroBanner = ({ onPlay }: HeroBannerProps) => {
  const { featuredContent } = useMovies();
  return (
    <div className="relative w-full h-[85vh] min-h-[500px]">
      <div className="absolute inset-0">
        <img
          src={heroImage}
          alt="Featured content"
          className="w-full h-full object-cover"
        />
        {/* Gradient overlays */}
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/60 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-background/30" />
      </div>

      <div className="relative z-10 flex flex-col justify-end h-full pb-32 px-8 md:px-12 max-w-2xl">
        <h1 className="text-5xl md:text-7xl font-extrabold mb-4 tracking-tight text-foreground drop-shadow-lg">
          STRANGER THINGS
        </h1>
        <p className="text-sm md:text-base text-foreground/85 mb-4 leading-relaxed max-w-lg">
          {featuredContent.description}
        </p>
        <div className="flex items-center gap-3 text-sm mb-5">
          <span className="text-netflix-green font-semibold">{featuredContent.match}% Match</span>
          <span className="border border-muted-foreground/40 px-1.5 py-0.5 text-xs text-muted-foreground">
            {featuredContent.rating}
          </span>
          <span className="text-muted-foreground">{featuredContent.seasons} Seasons</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onPlay(featuredContent.id)}
            className="flex items-center gap-2 bg-foreground text-background px-6 py-2.5 rounded font-semibold text-base hover:bg-foreground/80 transition-colors"
          >
            <Play size={20} fill="currentColor" />
            Play
          </button>
          <button className="flex items-center gap-2 bg-muted/70 text-foreground px-6 py-2.5 rounded font-semibold text-base hover:bg-muted/50 transition-colors">
            <Info size={20} />
            More Info
          </button>
        </div>
      </div>
    </div>
  );
};

export default HeroBanner;
