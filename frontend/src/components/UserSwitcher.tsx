import React from "react";
import { users } from "../data/content";
import { Plus, X } from "lucide-react";

interface UserSwitcherProps {
  currentUserId: number | null;
  isOpen: boolean;
  onSelect: (id: number) => void;
  onClose: () => void;
}

const UserSwitcher = ({ currentUserId, isOpen, onSelect, onClose }: UserSwitcherProps) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#141414]">
      <button
        type="button"
        onClick={onClose}
        className="absolute right-6 top-6 rounded-full border border-white/15 bg-black/40 p-2 text-white/80 transition hover:text-white"
        aria-label="Close profile switcher"
      >
        <X size={18} />
      </button>

      <div className="relative z-10 mx-auto flex w-full max-w-5xl flex-col items-center px-6 text-center">
        <div className="mb-10 flex flex-col items-center gap-3 md:mb-14">
          <span className="font-display text-5xl text-white md:text-6xl">Who&apos;s watching?</span>
          <p className="max-w-lg text-sm text-white/60 md:text-base">
            Profiles tune your ad personality and content vibe.
          </p>
        </div>

        <div className="flex flex-wrap items-start justify-center gap-8 md:gap-10">
          {users.map((user) => (
            <button
              key={user.id}
              type="button"
              title={user.vibe}
              onClick={() => onSelect(user.id)}
              className="group flex w-32 flex-col items-center gap-3 text-white/70 transition hover:text-white md:w-36"
            >
              <div
                className="relative flex h-28 w-28 items-center justify-center rounded-sm border border-white/10 text-3xl font-bold text-black shadow-[0_18px_40px_rgba(0,0,0,0.35)] transition group-hover:scale-[1.03] group-hover:border-white/40 md:h-32 md:w-32"
                style={{ backgroundColor: user.color }}
              >
                {user.key}
                {currentUserId === user.id && (
                  <span className="absolute -bottom-3 rounded-full border border-white/30 bg-black/70 px-2 py-0.5 text-[10px] uppercase tracking-[0.3em] text-white">
                    Active
                  </span>
                )}
              </div>
              <div className="flex flex-col items-center gap-1">
                <span className="text-sm font-medium text-white/80 group-hover:text-white">
                  {user.name}
                </span>
                <span className="text-[10px] uppercase tracking-[0.3em] text-white/45 group-hover:text-white/70">
                  {user.persona}
                </span>
              </div>
            </button>
          ))}

          <button
            type="button"
            className="group flex w-32 flex-col items-center gap-3 text-white/40 transition hover:text-white/70 md:w-36"
            aria-label="Add profile"
          >
            <div className="flex h-28 w-28 items-center justify-center rounded-sm border border-white/15 text-white/60 transition group-hover:border-white/50 md:h-32 md:w-32">
              <Plus size={28} />
            </div>
            <span className="text-sm">Add Profile</span>
          </button>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="mt-12 border border-white/40 px-6 py-2 text-xs uppercase tracking-[0.35em] text-white/70 transition hover:text-white"
        >
          Manage Profiles
        </button>
      </div>
    </div>
  );
};

export default UserSwitcher;
