import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ContentRow as ContentRowType } from "@/data/content";

interface ContentRowProps {
  row: ContentRowType;
  onItemClick: (id: string) => void;
}

const ContentRow = ({ row, onItemClick }: ContentRowProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      const amount = direction === "left" ? -600 : 600;
      scrollRef.current.scrollBy({ left: amount, behavior: "smooth" });
    }
  };

  return (
    <div className="mb-8 group/row">
      <h2 className="text-foreground font-semibold text-lg mb-2 px-8 md:px-12">{row.title}</h2>
      <div className="relative">
        {/* Left arrow */}
        <button
          onClick={() => scroll("left")}
          className="absolute left-0 top-0 bottom-0 z-10 w-10 bg-background/50 flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-opacity"
        >
          <ChevronLeft className="text-foreground" size={28} />
        </button>

        <div
          ref={scrollRef}
          className="flex gap-1.5 overflow-x-auto scrollbar-hide px-8 md:px-12"
        >
          {row.items.map((item, idx) => (
            <button
              key={`${item.id}-${idx}`}
              onClick={() => onItemClick(item.id)}
              className="flex-none w-[230px] group/card relative cursor-pointer"
            >
              <div className="overflow-hidden rounded-sm">
                <img
                  src={item.image}
                  alt={item.title}
                  className="w-full aspect-video object-cover transition-transform duration-300 group-hover/card:scale-110"
                  loading="lazy"
                />
              </div>
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background/90 to-transparent p-2 opacity-0 group-hover/card:opacity-100 transition-opacity">
                <p className="text-foreground text-xs font-medium truncate">{item.title}</p>
              </div>
            </button>
          ))}
        </div>

        {/* Right arrow */}
        <button
          onClick={() => scroll("right")}
          className="absolute right-0 top-0 bottom-0 z-10 w-10 bg-background/50 flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-opacity"
        >
          <ChevronRight className="text-foreground" size={28} />
        </button>
      </div>
    </div>
  );
};

export default ContentRow;
