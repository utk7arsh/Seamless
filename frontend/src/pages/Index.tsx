import { useState, useEffect, useCallback } from "react";
import Navbar from "@/components/Navbar";
import HeroBanner from "@/components/HeroBanner";
import ContentRow from "@/components/ContentRow";
import VideoViewer from "@/components/VideoViewer";
import UserSwitchToast from "@/components/UserSwitchToast";
import UserSwitcher from "@/components/UserSwitcher";
import { contentRows, users } from "@/data/content";
import { toast } from "sonner";

const Index = () => {
  const [currentUser, setCurrentUser] = useState<number | null>(null);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [resumeTime, setResumeTime] = useState<number | undefined>(undefined);
  const [showUserToast, setShowUserToast] = useState(false);
  const [isUserSwitcherOpen, setIsUserSwitcherOpen] = useState(true);

  // Auto-open video if returning from checkout with resume params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const resumeVideo = params.get("resumeVideo");
    const t = params.get("t");
    if (resumeVideo) {
      setVideoId(resumeVideo);
      setResumeTime(t ? Number(t) : undefined);
      if (params.get("checkout") === "success") {
        setTimeout(() => {
          toast.success("Order completed! Enjoy your movie.", { duration: 4000 });
        }, 500);
      }
      // Clean up URL without triggering a reload
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const switchUser = useCallback(() => {
    setCurrentUser((prev) => {
      const nextId = prev >= users.length ? 1 : prev + 1;
      return nextId;
    });
    setShowUserToast(true);
  }, []);

  const selectUser = (id: number) => {
    setCurrentUser(id);
    setIsUserSwitcherOpen(false);
    setShowUserToast(true);
  };

  useEffect(() => {
    if (showUserToast) {
      const timer = setTimeout(() => setShowUserToast(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [showUserToast]);

  const openVideo = (id: string) => {
    setResumeTime(undefined);
    setVideoId(id);
  };
  const closeVideo = () => {
    setResumeTime(undefined);
    setVideoId(null);
  };

  // If no user is selected and switcher isn't open, open it
  useEffect(() => {
    if (currentUser === null && !isUserSwitcherOpen) {
      setIsUserSwitcherOpen(true);
    }
  }, [currentUser, isUserSwitcherOpen]);

  return (
    <div className="min-h-screen bg-background">
      {currentUser && <Navbar currentUser={currentUser} onOpenProfiles={() => setIsUserSwitcherOpen(true)} />}
      <HeroBanner onPlay={openVideo} />

      <div className="-mt-24 relative z-10">
        {contentRows.map((row) => (
          <ContentRow key={row.title} row={row} onItemClick={openVideo} />
        ))}
      </div>

      {videoId && currentUser && <VideoViewer contentId={videoId} userId={currentUser} onClose={closeVideo} resumeTime={resumeTime} />}
      {showUserToast && <UserSwitchToast currentUser={currentUser} />}
      <UserSwitcher currentUserId={currentUser} isOpen={isUserSwitcherOpen} onSelect={selectUser} onClose={() => setIsUserSwitcherOpen(false)} />
    </div>
  );
};

export default Index;
