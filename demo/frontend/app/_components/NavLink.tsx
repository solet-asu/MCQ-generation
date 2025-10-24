"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils"; // if you have it; otherwise remove cn and inline classes

type Props = {
  href: string;
  children: React.ReactNode;
  className?: string;
};

export default function NavLink({ href, children, className }: Props) {
  const pathname = usePathname();
  const active = pathname === href;

  return (
    <Link
      href={href}
      className={cn(
        "relative px-2 py-1 text-sm text-muted-foreground hover:text-asu-maroon transition-colors",
        "after:absolute after:left-0 after:right-0 after:-bottom-[2px] after:h-[2px] after:rounded-full after:bg-transparent",
        "hover:after:bg-asu-maroon",
        active && "text-asu-maroon after:bg-asu-maroon",
        className
      )}
    >
      {children}
    </Link>
  );
}
