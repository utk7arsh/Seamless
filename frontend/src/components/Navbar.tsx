import { Search, Bell } from "lucide-react";
import { users } from "@/data/content";

interface NavbarProps {
  currentUser: number;
  onOpenProfiles: () => void;
}

const Navbar = ({ currentUser, onOpenProfiles }: NavbarProps) => {
  const user = users.find((u) => u.id === currentUser) || users[0];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-3 bg-gradient-to-b from-background/90 to-transparent">
      <div className="flex items-center gap-8">
        {/* Netflix Logo */}
        <span className="text-accent font-bold text-3xl tracking-wider">NETFLIX</span>
        <div className="hidden md:flex items-center gap-5">
          {["Home", "TV Shows", "Movies", "New & Popular", "My List"].map((item) => (
            <button
              key={item}
              className="text-sm text-foreground/80 hover:text-foreground transition-colors"
            >
              {item}
            </button>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button className="text-foreground hover:text-foreground/80 transition-colors">
          <Search size={20} />
        </button>
        <button className="relative text-foreground hover:text-foreground/80 transition-colors">
          <Bell size={20} />
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-accent rounded-full text-[8px] flex items-center justify-center text-accent-foreground">
            3
          </span>
        </button>
        <button
          type="button"
          onClick={onOpenProfiles}
          className="group flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-2 py-1 transition hover:border-white/30"
          aria-label="Switch profile"
        >
          <div
            className="w-8 h-8 rounded-sm flex items-center justify-center text-xs font-bold text-accent-foreground"
            style={{ backgroundColor: user.color }}
          >
            {user.key}
          </div>
          <div className="hidden flex-col items-start text-left sm:flex">
            <span className="text-xs uppercase tracking-[0.2em] text-foreground/60">{user.persona}</span>
            <span className="text-sm font-semibold text-foreground">{user.name}</span>
          </div>
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
