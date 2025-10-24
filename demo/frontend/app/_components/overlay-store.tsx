"use client";

import {
  createContext,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from "react";

type OverlayCtx = {
  open: boolean;
  show: () => void;
  hide: () => void;
  lastActiveEl: React.MutableRefObject<HTMLElement | null>;
};

const Ctx = createContext<OverlayCtx | null>(null);

export function OverlayProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const lastActiveEl = useRef<HTMLElement | null>(null);

  const show = () => {
    lastActiveEl.current = (document.activeElement as HTMLElement) ?? null;
    setOpen(true);
  };
  const hide = () => setOpen(false);

  return (
    <Ctx.Provider value={{ open, show, hide, lastActiveEl }}>
      {children}
    </Ctx.Provider>
  );
}

export function useOverlay() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useOverlay must be used within OverlayProvider");
  return v;
}
