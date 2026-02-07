import { useState, useEffect, useCallback } from "react";
import Navbar from "@/components/Navbar";
import HeroBanner from "@/components/HeroBanner";
import ContentRow from "@/components/ContentRow";
import VideoViewer from "@/components/VideoViewer";
import UserSwitchToast from "@/components/UserSwitchToast";
import { contentRows, users } from "@/data/content";

const Index = () => {
  const [currentUser, setCurrentUser] = useState(1);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [showUserToast, setShowUserToast] = useState(false);

  const switchUser = useCallback(() => {
    setCurrentUser((prev) => {
      const nextId = prev >= users.length ? 1 : prev + 1;
      return nextId;
    });
    setShowUserToast(true);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "]") {
        switchUser();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [switchUser]);

  useEffect(() => {
    if (showUserToast) {
      const timer = setTimeout(() => setShowUserToast(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [showUserToast]);

  const openVideo = (id: string) => setVideoId(id);
  const closeVideo = () => setVideoId(null);

  return (
    <div className="min-h-screen bg-background">
      <Navbar currentUser={currentUser} />
      <HeroBanner onPlay={openVideo} />

      <div className="-mt-24 relative z-10">
        {contentRows.map((row) => (
          <ContentRow key={row.title} row={row} onItemClick={openVideo} />
        ))}
      </div>

      {videoId && <VideoViewer contentId={videoId} onClose={closeVideo} />}
      {showUserToast && <UserSwitchToast currentUser={currentUser} />}
    </div>
  );
};

export default Index;
