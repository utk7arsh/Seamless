import React, { useRef, useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { X, Play, Pause, RotateCcw, RotateCw, ShoppingCart, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { allContent } from "@/data/content";
import { getAdsForContent, type AdSegment } from "@/data/contentAdSegments";
import { getProductsForContent } from "@/data/contentProducts";
import videoStrangerThings from "@/assets/video/STS3E4.mp4";
import videoBreakingBad from "@/assets/video/BBS3E2.mp4";
import adVideoElevenPepsi from "@/assets/video/elevenPepsi.mp4";
import adVideoKilngPizza from "@/assets/video/kilng_pizza_gen.mp4";

/** Resolve ad segment storagePath to a playable URL. Videos are imported from assets. */
function resolveAdVideoUrl(storagePath: string): string {
  const lower = storagePath.toLowerCase().replace(/\\/g, "/");
  if (lower.endsWith("elevenpepsi.mp4")) return adVideoElevenPepsi;
  if (lower.endsWith("kilng_pizza_gen.mp4")) return adVideoKilngPizza;
  return storagePath;
}

/** Videos are imported from src/assets/video/. */
function getVideoSrc(contentId: string): string {
  if (contentId === "1") return videoStrangerThings;   // Stranger Things S3 E4
  if (contentId === "2") return videoBreakingBad;      // Breaking Bad S3 E2
  return videoBreakingBad;
}

interface VideoViewerProps {
  contentId: string;
  /** Current user id (matches AppUser.id); used for user-segregated ad segments. */
  userId: number;
  onClose: () => void;
  resumeTime?: number;
}

// Netflix glowing bar: red strip on the RIGHT edge of the video viewer.
// To find it in this file, search for: "glowing bar" or "right-0" or "z-[95]".

const DEFAULT_AD_TIMING = 60;
const DEFAULT_AD_DURATION_SEC = 10;
const RIGHT_EDGE_HOVER_PERCENT = 20; // sidebar opens when cursor within this % of viewport width from right edge (during ad)
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

const VideoViewer = ({ contentId, userId, onClose }: VideoViewerProps) => {
  const content = allContent.find((c) => c.id === contentId);
  const timeOfAd = content?.ad_timing ?? DEFAULT_AD_TIMING;
  const adDurationSec = content?.ad_duration ?? DEFAULT_AD_DURATION_SEC;
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cartGlowTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [isPlaying, setIsPlaying] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showControls, setShowControls] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [cartGlow, setCartGlow] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  /** True until the video can start playing (lighter: we don't buffer the whole file upfront). */
  const [videoReady, setVideoReady] = useState(false);
  /** When true, the video element is playing an ad from contentAdSegments; we cut back at ad end. */
  const [isPlayingAd, setIsPlayingAd] = useState(false);
  /** Main video: from @/data/content (content.video) or getVideoSrc fallback. */
  const mainVideoSrc = content?.video ?? getVideoSrc(contentId);
  const [videoSrc, setVideoSrc] = useState(() => mainVideoSrc);
  const mainVideoSrcRef = useRef<string>("");
  const mainResumeTimeRef = useRef(0);
  const mainDurationRef = useRef(0);
  const pendingResumeRef = useRef(false);
  const currentAdSegmentRef = useRef<AdSegment | null>(null);
  const adSlotTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const video = videoRef.current;
  const adSegments = getAdsForContent(contentId, userId);
  const products = getProductsForContent(contentId);
  const featuredProduct = products[0]; // Show only the first product
  const inAdSlot =
    !isPlayingAd &&
    adSegments.some(
      (seg) => currentTime >= seg.startTime && currentTime < seg.endTime
    );
  const currentSegment =
    !isPlayingAd &&
    adSegments.find(
      (seg) => currentTime >= seg.startTime && currentTime < seg.endTime
    );
  /** True when we're in any ad segment (main timeline) or playing an ad; used for cart sidebar and right-edge glow. */
  const isAdZone = inAdSlot || isPlayingAd;

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

  // When opening different content, reset to main video
  useEffect(() => {
    if (adSlotTimerRef.current) {
      clearTimeout(adSlotTimerRef.current);
      adSlotTimerRef.current = null;
    }
    setVideoSrc(mainVideoSrc);
    setIsPlayingAd(false);
    pendingResumeRef.current = false;
    currentAdSegmentRef.current = null;
    setVideoReady(false);
  }, [contentId, mainVideoSrc]);

  // VIDEO EVENT LISTENERS
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const onTimeUpdate = () => setCurrentTime(v.currentTime);
    const onLoadedMetadata = () => {
      setDuration(v.duration);
      if (!isPlayingAd) mainDurationRef.current = v.duration;
      if (pendingResumeRef.current) {
        v.currentTime = mainResumeTimeRef.current;
        setCurrentTime(mainResumeTimeRef.current);
        setDuration(mainDurationRef.current);
        pendingResumeRef.current = false;
        v.play().catch(() => {});
        setIsPlaying(true);
        setVideoReady(true);
      }
    };
    const onCanPlay = () => setVideoReady(true);
    const onEnded = () => {
      if (isPlayingAd && currentAdSegmentRef.current) {
        if (adSlotTimerRef.current) {
          clearTimeout(adSlotTimerRef.current);
          adSlotTimerRef.current = null;
        }
        const seg = currentAdSegmentRef.current;
        mainVideoSrcRef.current = mainVideoSrc;
        mainResumeTimeRef.current = seg.endTime;
        mainDurationRef.current = duration;
        pendingResumeRef.current = true;
        currentAdSegmentRef.current = null;
        setVideoSrc(mainVideoSrc);
        setIsPlayingAd(false);
      } else {
        setIsPlaying(false);
      }
    };
    v.addEventListener("timeupdate", onTimeUpdate);
    v.addEventListener("loadedmetadata", onLoadedMetadata);
    v.addEventListener("canplay", onCanPlay);
    v.addEventListener("ended", onEnded);
    return () => {
      v.removeEventListener("timeupdate", onTimeUpdate);
      v.removeEventListener("loadedmetadata", onLoadedMetadata);
      v.removeEventListener("canplay", onCanPlay);
      v.removeEventListener("ended", onEnded);
    };
  }, [isPlayingAd, mainVideoSrc, duration]);

  // Seamless cut to ad when playback enters any ad segment. Ad plays for (endTime - startTime) only, then we resume at endTime.
  useEffect(() => {
    if (!inAdSlot || !currentSegment) return;
    const v = videoRef.current;
    if (!v) return;
    mainVideoSrcRef.current = mainVideoSrc;
    mainResumeTimeRef.current = currentSegment.endTime;
    mainDurationRef.current = duration;
    currentAdSegmentRef.current = currentSegment;
    setVideoSrc(resolveAdVideoUrl(currentSegment.storagePath));
    setIsPlayingAd(true);
    setVideoReady(false);

    const slotDurationMs = (currentSegment.endTime - currentSegment.startTime) * 1000;
    adSlotTimerRef.current = setTimeout(() => {
      adSlotTimerRef.current = null;
      if (!currentAdSegmentRef.current) return;
      const seg = currentAdSegmentRef.current;
      mainVideoSrcRef.current = mainVideoSrc;
      mainResumeTimeRef.current = seg.endTime;
      mainDurationRef.current = duration;
      pendingResumeRef.current = true;
      currentAdSegmentRef.current = null;
      setVideoSrc(mainVideoSrc);
      setIsPlayingAd(false);
    }, slotDurationMs);

    const t = setTimeout(() => {
      videoRef.current?.play().catch(() => {});
    }, 0);
    return () => {
      clearTimeout(t);
      // Do NOT clear adSlotTimerRef here: when we set isPlayingAd(true), inAdSlot becomes false
      // and this cleanup runs, which was cancelling the timer. Timer is cleared only when we
      // cut back (in the timer callback or onEnded) or when contentId changes.
    };
  }, [inAdSlot, currentSegment, mainVideoSrc, duration]);

  // CLEANUP
  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
      if (cartGlowTimeoutRef.current) clearTimeout(cartGlowTimeoutRef.current);
    };
  }, []);

  // CART GLOW: Trigger when ad starts playing
  useEffect(() => {
    if (isPlayingAd) {
      if (cartGlowTimeoutRef.current) clearTimeout(cartGlowTimeoutRef.current);
      setCartGlow(true);
      cartGlowTimeoutRef.current = setTimeout(() => {
        setCartGlow(false);
        cartGlowTimeoutRef.current = null;
      }, 2000);
    }
  }, [isPlayingAd]);

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
      {/* Video: preload=metadata so we don't download the whole file until play; loading state until canplay */}
      {!videoReady && (
        <div className="absolute inset-0 z-[5] flex items-center justify-center bg-black">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-white/30 border-t-white rounded-full animate-spin" aria-hidden />
            <p className="text-white/80 text-sm">Loading video…</p>
          </div>
        </div>
      )}
      <video
        ref={videoRef}
        src={videoSrc}
        className="absolute inset-0 w-full h-full object-contain"
        preload="metadata"
        autoPlay
        playsInline
        onClick={togglePlay}
        onCanPlay={() => setVideoReady(true)}
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
          setCheckoutError(null);
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
      {isAdZone && (
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
          {/* Glowing segments: one per ad, each with its color from contentAdSegments.json */}
          {!isPlayingAd &&
            duration > 0 &&
            adSegments.map((seg) => {
              if (seg.endTime > duration) return null;
              const left = (seg.startTime / duration) * 100;
              const width = ((seg.endTime - seg.startTime) / duration) * 100;
              return (
                <div
                  key={`${seg.startTime}-${seg.endTime}`}
                  className="absolute h-1.5 rounded-md pointer-events-none"
                  style={{
                    left: `${left}%`,
                    width: `${width}%`,
                    backgroundColor: seg.color ?? "#f59e0b",
                    boxShadow: `0 0 12px ${seg.color ?? "#f59e0b"}80`,
                    border: `1px solid ${seg.color ?? "#f59e0b"}cc`,
                  }}
                  aria-hidden
                  title="Ad slot"
                />
              );
            })}
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
              <div className="flex-1 overflow-y-auto p-4">
                {featuredProduct ? (
                  <div className="flex flex-col gap-4">
                    {/* Product card - grocery checkout style */}
                    <div className="bg-neutral-800 rounded-lg overflow-hidden border border-neutral-700">
                      <div className="p-4">
                        <h3 className="text-lg font-semibold text-white mb-2">
                          {featuredProduct.product}
                        </h3>
                        <p className="text-neutral-300 text-sm mb-4 leading-relaxed">
                          {featuredProduct.description}
                        </p>
                        <div className="flex items-baseline gap-2 mb-4">
                          <span className="text-3xl font-bold text-white">
                            ${featuredProduct.price.toFixed(2)}
                          </span>
                          <span className="text-sm text-neutral-400">each</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-neutral-400">
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            In Stock
                          </span>
                          <span>•</span>
                          <span>Ready for pickup</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Order summary */}
                    <div className="bg-neutral-800/50 rounded-lg p-4 border border-neutral-700">
                      <h4 className="text-sm font-semibold text-white mb-3">Order Summary</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between text-neutral-300">
                          <span>Subtotal</span>
                          <span>${featuredProduct.price.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between text-neutral-300">
                          <span>Tax</span>
                          <span>${(featuredProduct.price * 0.08).toFixed(2)}</span>
                        </div>
                        <div className="border-t border-neutral-600 pt-2 mt-2">
                          <div className="flex justify-between text-white font-semibold text-base">
                            <span>Total</span>
                            <span>${(featuredProduct.price * 1.08).toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-neutral-400 text-sm text-center py-8">
                    No products available for this content.
                  </div>
                )}
              </div>
              <div className="p-4 border-t border-neutral-700">
                {featuredProduct ? (
                  <a
                    href={featuredProduct.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full py-3 px-4 rounded-md bg-red-600 text-white font-semibold hover:bg-red-500 transition-colors text-center"
                    onClick={() => { isHoveringSidebarRef.current = false; setSidebarOpen(false); }}
                  >
                    Buy Now at Kroger
                  </a>
                ) : (
                  <button
                    type="button"
                    onClick={() => { isHoveringSidebarRef.current = false; setSidebarOpen(false); }}
                    className="w-full py-3 px-4 rounded-md bg-neutral-700 text-neutral-400 font-semibold cursor-not-allowed"
                    disabled
                  >
                    No Products Available
                  </button>
                )}
              </div>
            </aside>
          </>,
          document.body
        )}
    </div>
  );
};

export default VideoViewer;
