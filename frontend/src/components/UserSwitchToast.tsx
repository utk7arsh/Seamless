import { users } from "@/data/content";

interface UserSwitchToastProps {
  currentUser: number;
}

const UserSwitchToast = ({ currentUser }: UserSwitchToastProps) => {
  const user = users.find((u) => u.id === currentUser) || users[0];

  return (
    <div className="fixed top-20 right-8 z-[90] bg-card border border-border px-4 py-3 rounded-sm flex items-center gap-3 animate-in fade-in slide-in-from-right-5 duration-300">
      <div
        className="w-8 h-8 rounded-sm flex items-center justify-center text-sm font-bold text-accent-foreground"
        style={{ backgroundColor: user.color }}
      >
        {user.key}
      </div>
      <span className="text-foreground text-sm font-medium">Switched to {user.name}</span>
    </div>
  );
};

export default UserSwitchToast;
