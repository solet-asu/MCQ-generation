"use client";

import { useLayoutEffect } from "react";

export function useLockBodyScroll(locked: boolean) {
  useLayoutEffect(() => {
    const body = document.body;
    const html = document.documentElement;
    const prevBodyOverflow = body.style.overflow;
    const prevHtmlOverflow = html.style.overflow;

    if (locked) {
      body.style.overflow = "hidden";
      html.style.overflow = "hidden";
    } else {
      body.style.overflow = prevBodyOverflow;
      html.style.overflow = prevHtmlOverflow;
    }

    return () => {
      body.style.overflow = prevBodyOverflow;
      html.style.overflow = prevHtmlOverflow;
    };
  }, [locked]);
}
