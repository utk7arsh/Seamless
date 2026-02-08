import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import HeroBanner from "@/components/HeroBanner";
import ContentRow from "@/components/ContentRow";
import VideoViewer from "@/components/VideoViewer";
import UserSwitchToast from "@/components/UserSwitchToast";
import UserSwitcher from "@/components/UserSwitcher";
import { contentRows, users } from "@/data/content";

const Index = () => {
  const [currentUser, setCurrentUser] = useState<number | null>(null);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [showUserToast, setShowUserToast] = useState(false);
  const [isUserSwitcherOpen, setIsUserSwitcherOpen] = useState(true);

  const activeUserId = currentUser ?? users[0].id;

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

  const openVideo = (id: string) => setVideoId(id);
  const closeVideo = () => setVideoId(null);

  return (
    <div className="min-h-screen bg-background">
      <Navbar currentUser={activeUserId} onOpenProfiles={() => setIsUserSwitcherOpen(true)} />
      <HeroBanner onPlay={openVideo} />

      <div className="-mt-24 relative z-10">
        {contentRows.map((row) => (
          <ContentRow key={row.title} row={row} onItemClick={openVideo} />
        ))}
      </div>

      {videoId && <VideoViewer contentId={videoId} userId={activeUserId} onClose={closeVideo} />}
      {showUserToast && <UserSwitchToast currentUser={activeUserId} />}
      <UserSwitcher
        currentUserId={currentUser}
        isOpen={isUserSwitcherOpen}
        onSelect={selectUser}
        onClose={() => setIsUserSwitcherOpen(false)}
      />
    </div>
  );
};

export default Index;
