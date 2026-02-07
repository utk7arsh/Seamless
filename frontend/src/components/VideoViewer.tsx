import React, { useRef, useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { X, Play, Pause, RotateCcw, RotateCw, ShoppingCart } from "lucide-react";
import { allContent } from "@/data/content";
import sampleVideo from "@/assets/video/breaking_bad.mp4";

interface VideoViewerProps {
  contentId: string;
  onClose: () => void;
}

// Netflix glowing bar: red strip on the RIGHT edge of the video viewer.
// To find it in this file, search for: "glowing bar" or "right-0" or "z-[95]".

const time_of_ad = 60;
const AD_DURATION_SEC = 10; // pretend ad plays for 10 seconds
const RIGHT_EDGE_HOVER_PERCENT = 10; // sidebar opens when cursor within this % of viewport width from right edge (during ad)
const SEEK_AMOUNT = 10;
const CONTROLS_HIDE_DELAY = 3000;

// NETFLIX GLOW BAR: The red glowing strip on the RIGHT edge of the video viewer
// is rendered in the return() below — search for "glowing bar" or "right-0" or "z-[95]"

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const VideoViewer = ({ contentId, onClose }: VideoViewerProps) => {
  const content = allContent.find((c) => c.id === contentId);
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cartGlowTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [isPlaying, setIsPlaying] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showControls, setShowControls] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [cartGlow, setCartGlow] = useState(false);

  const video = videoRef.current;

  const togglePlay = useCallback(() => {
    if (!video) return;
    if (video.paused) {
      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  }, [video]);

  const rewind = useCallback(() => {
    if (!video) return;
    video.currentTime = Math.max(0, video.currentTime - SEEK_AMOUNT);
  }, [video]);

  const forward = useCallback(() => {
    if (!video) return;
    video.currentTime = Math.min(video.duration, video.currentTime + SEEK_AMOUNT);
  }, [video]);

  const handleSeek = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!video) return;
      const value = Number(e.target.value);
      video.currentTime = value;
      setCurrentTime(value);
    },
    [video]
  );

  const resetControlsTimer = useCallback(() => {
    setShowControls(true);
    if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
    controlsTimeoutRef.current = setTimeout(() => {
      if (videoRef.current && !videoRef.current.paused) setShowControls(false);
      controlsTimeoutRef.current = null;
    }, CONTROLS_HIDE_DELAY);
  }, []);

  const isAdZone = duration > 0 && currentTime >= time_of_ad && currentTime < time_of_ad + AD_DURATION_SEC;

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      resetControlsTimer();
      if (isAdZone) {
        const rightZonePx = window.innerWidth * (RIGHT_EDGE_HOVER_PERCENT / 100);
        const nearRightEdge = e.clientX >= window.innerWidth - rightZonePx;
        setSidebarOpen(nearRightEdge);
      }
    },
    [resetControlsTimer, isAdZone]
  );

  const handleMouseLeave = useCallback(() => {
    if (videoRef.current && !videoRef.current.paused) setShowControls(false);
    if (isAdZone) setSidebarOpen(false);
  }, [isAdZone]);

  const wasAdZoneRef = useRef(false);
  const isHoveringSidebarRef = useRef(false);
  useEffect(() => {
    if (wasAdZoneRef.current && !isAdZone) {
      if (!isHoveringSidebarRef.current) setSidebarOpen(false);
    }
    wasAdZoneRef.current = isAdZone;
  }, [isAdZone]);

  // VIDEO EVENT LISTENERS
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const onTimeUpdate = () => setCurrentTime(v.currentTime);
    const onLoadedMetadata = () => setDuration(v.duration);
    const onEnded = () => setIsPlaying(false);
    v.addEventListener("timeupdate", onTimeUpdate);
    v.addEventListener("loadedmetadata", onLoadedMetadata);
    v.addEventListener("ended", onEnded);
    return () => {
      v.removeEventListener("timeupdate", onTimeUpdate);
      v.removeEventListener("loadedmetadata", onLoadedMetadata);
      v.removeEventListener("ended", onEnded);
    };
  }, []);

  // CLEANUP
  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
      if (cartGlowTimeoutRef.current) clearTimeout(cartGlowTimeoutRef.current);
    };
  }, []);

  // KEYBOARD SHORTCUTS
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (sidebarOpen) setSidebarOpen(false);
        else onClose();
      }
      if (e.key === " ") {
        e.preventDefault();
        togglePlay();
      }
      if (e.key === "[") {
        e.preventDefault();
        if (cartGlowTimeoutRef.current) clearTimeout(cartGlowTimeoutRef.current);
        setCartGlow(true);
        cartGlowTimeoutRef.current = setTimeout(() => {
          setCartGlow(false);
          cartGlowTimeoutRef.current = null;
        }, 2000);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, togglePlay, sidebarOpen]);

  return (
    <div
      className="fixed inset-0 z-[100] bg-black flex flex-col"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Layout order: Video, then top bar (close), cart, GLOW BAR (right edge), center play, bottom bar, cart sidebar portal */}

      {/* Video */}
      <video
        ref={videoRef}
        src={sampleVideo}
        className="absolute inset-0 w-full h-full object-contain"
        autoPlay
        playsInline
        onClick={togglePlay}
      />

      {/* Top bar: close */}
      <div
        className={`
          absolute top-0 left-0 right-0 z-10
          flex items-center justify-end p-4
          bg-gradient-to-b from-black/70 to-transparent
          transition-opacity duration-300
          ${showControls ? "opacity-100" : "opacity-0 pointer-events-none"}
        `}
      >
        <button
          onClick={onClose}
          className="p-2 rounded-full text-white/90 hover:text-white hover:bg-white/10 transition-colors"
          aria-label="Close"
        >
          <X size={28} />
        </button>
      </div>

      {/* Shopping cart: corner icon, moves up when timeline is visible (z-20 so always clickable); "[" glows it */}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setSidebarOpen(true);
        }}
        className={`
          absolute right-4 z-20
          p-2 rounded-lg
          bg-white/10 text-white/80 hover:bg-white/20 hover:text-white transition-all duration-300
          ${showControls ? "bottom-28 opacity-100" : "bottom-4 opacity-70"}
          ${cartGlow ? "ring-2 ring-red-500 ring-offset-2 ring-offset-black shadow-[0_0_20px_rgba(239,68,68,0.6)]" : ""}
        `}
        aria-label="Cart"
      >
        <ShoppingCart size={22} />
      </button>

      {/* ========== NETFLIX-STYLE GLOWING BAR — RIGHT SIDE OF SCREEN ==========
          FIND IT: search this file for "glowing bar" or "right-0" or "z-[95]"
          Location: RIGHT SIDE of the video viewer, full height.
          This is the red glow strip (like Google Gemini in Chrome).
          Search for: "glowing bar" or "right-0" or "z-[95]" to find it.
          Styling: Netflix red (#E50914), gradient + box-shadow glow. */}
      {currentTime >= time_of_ad && currentTime < time_of_ad + AD_DURATION_SEC && duration > time_of_ad && (
      <div
        className="fixed right-0 top-0 bottom-0 w-[10px] pointer-events-none z-[95] animate-in fade-in duration-500"
        style={{
          background: "linear-gradient(to left,rgba(229,9,20,0.9) 0%,"+
                          " rgba(229,9,20,0.35) 60%, transparent 100%)",
          boxShadow: "-32px 0 160px rgba(229,9,20,0.7), -16px 0 96px rgba(229,9,20,0.6), -8px 0 48px rgba(229,9,20,0.5)",
        }}
        aria-hidden
      />
      )}
      {/* Center play/pause (big) when paused */}
      {!isPlaying && (
        <button
          onClick={togglePlay}
          className="absolute inset-0 z-10 flex items-center justify-center bg-black/20 transition-opacity hover:bg-black/30"
          aria-label="Play"
        >
          <div className="w-20 h-20 rounded-full bg-white/90 flex items-center justify-center shadow-lg hover:scale-105 transition-transform">
            <Play size={40} className="text-black ml-1" fill="currentColor" />
          </div>
        </button>
      )}

      {/* Bottom play bar */}
      <div
        className={`
          absolute bottom-0 left-0 right-0 z-10
          pt-12 pb-4 px-4 md:px-6
          bg-gradient-to-t from-black/90 via-black/50 to-transparent
          transition-opacity duration-300
          ${showControls ? "opacity-100" : "opacity-0 pointer-events-none"}
        `}
      >
        {/* Seek bar with red history bar (watched progress) */}
        <div className="mb-3 relative h-6 flex items-center">
          {/* Gray track background */}
          <div className="absolute left-0 right-0 h-1.5 rounded-full bg-white/20" aria-hidden />
          {/* Red history bar: watched portion */}
          <div
            className="absolute left-0 h-1.5 rounded-l-full bg-red-600 transition-[width] duration-100"
            style={{ width: duration ? `${(currentTime / duration) * 100}%` : "0%" }}
            aria-hidden
          />
          {/* Yellow blob: 10-second ad segment on timeline */}
          {duration > 0 && time_of_ad < duration && (
            <div
              className="absolute top-1/2 h-1.5 rounded-sm bg-yellow-400/90 shadow-[0_0_6px_rgba(250,204,21,0.6)] pointer-events-none"
              style={{
                left: `${(time_of_ad / duration) * 100}%`,
                width: `${Math.min((AD_DURATION_SEC / duration) * 100, ((duration - time_of_ad) / duration) * 100)}%`,
                transform: "translateY(-50%)",
              }}
              aria-hidden
            />
          )}
          <input
            type="range"
            min={0}
            max={duration || 100}
            value={currentTime}
            onChange={handleSeek}
            className="relative w-full h-6 appearance-none cursor-pointer bg-transparent [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-red-600 [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:shadow-md hover:[&::-webkit-slider-thumb]:scale-110 [&::-webkit-slider-runnable-track]:bg-transparent"
            aria-label="Seek"
          />
        </div>

        <div className="flex items-center gap-4">
          {/* Left: rewind, play/pause, forward */}
          <div className="flex items-center gap-2">
            <button
              onClick={rewind}
              className="p-2 rounded-full text-white/90 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Rewind 10 seconds"
            >
              <RotateCcw size={24} />
            </button>
            <button
              onClick={togglePlay}
              className="p-2 rounded-full text-white/90 hover:text-white hover:bg-white/10 transition-colors"
              aria-label={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? <Pause size={28} /> : <Play size={28} fill="currentColor" />}
            </button>
            <button
              onClick={forward}
              className="p-2 rounded-full text-white/90 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Forward 10 seconds"
            >
              <RotateCw size={24} />
            </button>
          </div>

          {/* Time */}
          <span className="text-white/90 text-sm tabular-nums">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>

          <div className="flex-1" />

          {/* Title (optional, subtle) */}
          {content && (
            <span className="text-white/80 text-sm font-medium truncate max-w-[200px] hidden sm:block">
              {content.title}
            </span>
          )}
        </div>
      </div>

      {/* Cart sidebar: render via portal so it appears above everything */}
      {typeof document !== "undefined" &&
        createPortal(
          <>
            <div
              role="presentation"
              className={`fixed inset-0 z-[200] bg-black/50 transition-opacity duration-300 ${sidebarOpen ? "opacity-100" : "opacity-0 pointer-events-none"}`}
              onClick={() => { isHoveringSidebarRef.current = false; setSidebarOpen(false); }}
            />
            <aside
              className={`fixed top-0 right-0 bottom-0 z-[210] w-full max-w-sm bg-neutral-900 border-l border-neutral-700 shadow-xl flex flex-col transition-transform duration-300 ease-out ${sidebarOpen ? "translate-x-0" : "translate-x-full"}`}
              aria-hidden={!sidebarOpen}
              onMouseEnter={() => { isHoveringSidebarRef.current = true; }}
              onMouseLeave={() => { isHoveringSidebarRef.current = false; setSidebarOpen(false); }}
            >
              <div className="flex items-center justify-between p-4 border-b border-neutral-700">
                <h2 className="text-lg font-semibold text-white">Cart</h2>
                <button
                  type="button"
                  onClick={() => { isHoveringSidebarRef.current = false; setSidebarOpen(false); }}
                  className="p-2 rounded-full text-neutral-400 hover:text-white hover:bg-neutral-700 transition-colors"
                  aria-label="Close cart"
                >
                  <X size={20} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4 text-neutral-300 text-sm leading-relaxed">
                <p className="mb-4">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
                </p>
                <p className="mb-4">
                  Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
                </p>
                <p>
                  Curabitur pretium tincidunt lacus. Nulla facilisi. Ut convallis, sem sit amet interdum consectetuer, odio augue aliquam leo, nec dapibus tortor nibh sed augue.
                </p>
              </div>
              <div className="p-4 border-t border-neutral-700">
                <button
                  type="button"
                  onClick={() => { isHoveringSidebarRef.current = false; setSidebarOpen(false); }}
                  className="w-full py-3 px-4 rounded-md bg-red-600 text-white font-semibold hover:bg-red-500 transition-colors"
                >
                  Checkout
                </button>
              </div>
            </aside>
          </>,
          document.body
        )}
    </div>
  );
};

export default VideoViewer;
