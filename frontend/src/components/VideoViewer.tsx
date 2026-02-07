import React, { useRef, useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { X, Play, Pause, RotateCcw, RotateCw, ShoppingCart, Loader2 } from "lucide-react";
import { allContent } from "@/data/content";
import sampleVideo from "@/assets/video/breaking_bad.mp4";
import { toast } from "sonner";

interface VideoViewerProps {
  contentId: string;
  onClose: () => void;
  resumeTime?: number;
}

const SEEK_AMOUNT = 10;
const CONTROLS_HIDE_DELAY = 3000;

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const VideoViewer = ({ contentId, onClose, resumeTime }: VideoViewerProps) => {
  const content = allContent.find((c) => c.id === contentId);
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [isPlaying, setIsPlaying] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showControls, setShowControls] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);

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

  const handleCheckout = useCallback(async () => {
    const apiKey = import.meta.env.VITE_FLOWGLAD_API_KEY;
    if (!apiKey || apiKey === "your_flowglad_api_key_here") {
      const msg = "Flowglad API key is not configured. Add VITE_FLOWGLAD_API_KEY to frontend/.env.local";
      setCheckoutError(msg);
      toast.error(msg);
      return;
    }

    setCheckoutLoading(true);
    setCheckoutError(null);

    try {
      const videoTime = videoRef.current?.currentTime ?? 0;
      const baseUrl = window.location.origin + window.location.pathname;
      const resumeUrl = `${baseUrl}?resumeVideo=${encodeURIComponent(contentId)}&t=${Math.floor(videoTime)}`;
      const successResumeUrl = `${resumeUrl}&checkout=success`;

      const res = await fetch("/api/flowglad/checkout-sessions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          checkoutSession: {
            type: "product",
            anonymous: true,
            customerExternalId: null,
            priceSlug: "papa_john_s_pizza",
            successUrl: successResumeUrl,
            cancelUrl: resumeUrl,
            quantity: 1,
          },
        }),
      });

      if (!res.ok) {
        const body = await res.text();
        throw new Error(`Checkout failed (${res.status}): ${body}`);
      }

      const data = await res.json();
      const checkoutUrl = data?.checkoutSession?.url ?? data?.url;
      if (!checkoutUrl) {
        throw new Error("No checkout URL returned from Flowglad");
      }

      window.location.href = checkoutUrl;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Checkout failed";
      setCheckoutError(msg);
      toast.error(msg);
    } finally {
      setCheckoutLoading(false);
    }
  }, []);

  const resetControlsTimer = useCallback(() => {
    setShowControls(true);
    if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
    controlsTimeoutRef.current = setTimeout(() => {
      if (videoRef.current && !videoRef.current.paused) setShowControls(false);
      controlsTimeoutRef.current = null;
    }, CONTROLS_HIDE_DELAY);
  }, []);

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const onTimeUpdate = () => setCurrentTime(v.currentTime);
    const onLoadedMetadata = () => {
      setDuration(v.duration);
      if (resumeTime != null && resumeTime > 0) {
        v.currentTime = resumeTime;
        v.play();
        setIsPlaying(true);
      }
    };
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

  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
    };
  }, []);

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
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, togglePlay, sidebarOpen]);

  return (
    <div
      className="fixed inset-0 z-[100] bg-black flex flex-col"
      onMouseMove={resetControlsTimer}
      onMouseLeave={() => {
        if (videoRef.current && !videoRef.current.paused) setShowControls(false);
      }}
    >
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

      {/* Shopping cart: corner icon, moves up when timeline is visible (z-20 so always clickable) */}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setCheckoutError(null);
          setSidebarOpen(true);
        }}
        className={`
          absolute right-4 z-20
          p-2 rounded-lg
          bg-white/10 text-white/80 hover:bg-white/20 hover:text-white transition-all duration-300
          ${showControls ? "bottom-28 opacity-100" : "bottom-4 opacity-70"}
        `}
        aria-label="Cart"
      >
        <ShoppingCart size={22} />
      </button>

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
        {/* Seek bar */}
        <div className="mb-3">
          <input
            type="range"
            min={0}
            max={duration || 100}
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-white/30 accent-red-600 hover:accent-red-500 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-red-600 [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:transition-transform hover:[&::-webkit-slider-thumb]:scale-110"
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
              onClick={() => setSidebarOpen(false)}
            />
            <aside
              className={`fixed top-0 right-0 bottom-0 z-[210] w-full max-w-sm bg-neutral-900 border-l border-neutral-700 shadow-xl flex flex-col transition-transform duration-300 ease-out ${sidebarOpen ? "translate-x-0" : "translate-x-full"}`}
              aria-hidden={!sidebarOpen}
            >
              <div className="flex items-center justify-between p-4 border-b border-neutral-700">
                <h2 className="text-lg font-semibold text-white">Cart</h2>
                <button
                  type="button"
                  onClick={() => setSidebarOpen(false)}
                  className="p-2 rounded-full text-neutral-400 hover:text-white hover:bg-neutral-700 transition-colors"
                  aria-label="Close cart"
                >
                  <X size={20} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4 text-neutral-300 text-sm leading-relaxed">
                {/* Product card */}
                <div className="rounded-lg border border-neutral-700 bg-neutral-800 p-4 mb-4">
                  <div className="flex gap-3">
                    <div className="w-16 h-16 rounded-md bg-neutral-700 flex items-center justify-center text-3xl flex-shrink-0">
                      🍕
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-white font-semibold text-base">Papa John's Pizza</h3>
                      <p className="text-neutral-400 text-xs mt-0.5">Large Original Crust - Pepperoni</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-white font-bold text-lg">$12.99</span>
                        <span className="text-neutral-400 text-xs">Qty: 1</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Order summary */}
                <div className="border-t border-neutral-700 pt-3 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-neutral-400">Subtotal</span>
                    <span className="text-white">$12.99</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">Tax</span>
                    <span className="text-neutral-400 text-xs">Calculated at checkout</span>
                  </div>
                  <div className="flex justify-between border-t border-neutral-700 pt-2 mt-2">
                    <span className="text-white font-semibold">Total</span>
                    <span className="text-white font-semibold">$12.99</span>
                  </div>
                </div>
              </div>
              <div className="p-4 border-t border-neutral-700">
                {checkoutError && (
                  <p className="text-red-400 text-xs mb-2 text-center">{checkoutError}</p>
                )}
                <button
                  type="button"
                  onClick={handleCheckout}
                  disabled={checkoutLoading}
                  className="w-full py-3 px-4 rounded-md bg-red-600 text-white font-semibold hover:bg-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {checkoutLoading ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      Processing...
                    </>
                  ) : (
                    "Checkout"
                  )}
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
