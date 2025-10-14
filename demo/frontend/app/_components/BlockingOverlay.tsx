"use client";

import { useEffect, useRef } from "react";
import { Sparkles } from "lucide-react";
import ClientPortal from "./ClientPortal";
import { useLockBodyScroll } from "./useLockBodyScroll";
import { useOverlay } from "./overlay-store";

export default function BlockingOverlay({
  message,
  onAbort,
}: {
  message: string;
  onAbort?: () => void;
}) {
  const { open, lastActiveEl } = useOverlay();
  useLockBodyScroll(open);

  const overlayRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (open) {
      overlayRef.current?.focus();
    } else {
      lastActiveEl.current?.focus?.();
    }
  }, [open, lastActiveEl]);

  if (!open) return null;

  return (
    <ClientPortal>
      <div
        ref={overlayRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={message}
        className="fixed inset-0 z-[10000] h-[100dvh] w-[100dvw] bg-black/70 backdrop-blur-sm flex items-center justify-center"
      >
        {/* soft radial glow in the background */}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.12),transparent_60%)]" />

        <div className="relative z-10 text-center space-y-8">
          {/* spinner ring + pulse + icon */}
          <div className="relative">
            <div className="w-32 h-32 mx-auto relative">
              <div
                className="absolute inset-0 border-4 border-white/25 rounded-full animate-spin"
                style={{ animationDuration: "2s" }}
              />
              <div className="absolute inset-4 bg-white/10 rounded-full animate-pulse" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Sparkles className="w-12 h-12 text-white/90 animate-pulse" />
              </div>
            </div>
          </div>

          {/* title + cute bouncing dots */}
          <div className="space-y-3">
            <h2 className="text-2xl font-bold text-white">{message}</h2>

            {/* the dots */}
            <div
              className="flex items-center justify-center gap-2"
              aria-hidden="true"
            >
              <div
                className="w-2 h-2 bg-white rounded-full animate-bounce"
                style={{ animationDelay: "0ms" }}
              />
              <div
                className="w-2 h-2 bg-white rounded-full animate-bounce"
                style={{ animationDelay: "150ms" }}
              />
              <div
                className="w-2 h-2 bg-white rounded-full animate-bounce"
                style={{ animationDelay: "300ms" }}
              />
            </div>
            <span className="sr-only">Loading…</span>

            <p className="text-white/75 text-sm">
              Analyzing your text and crafting questions…
            </p>
          </div>

          {/* Abort button */}
          {onAbort && (
            <div className="mt-2">
              <button
                type="button"
                onClick={() => {
                  try {
                    onAbort();
                  } catch {}
                }}
                className="inline-flex items-center px-4 py-2 rounded-md  bg-white/10 hover:bg-white/20 
                 text-white text-sm focus:outline-none focus:ring-2 focus:ring-white/50 transition-colors cursor-pointer"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </ClientPortal>
  );
}
