import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Info, HelpCircle } from "lucide-react";
import HomeClient from "./_components/HomeClient";
import { OverlayProvider } from "./_components/overlay-store";
import BlockingOverlay from "./_components/BlockingOverlay";
import NavLink from "./_components/NavLink";
import Image from "next/image";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <OverlayProvider>
        <header className="border-b border-border bg-card">
          <div className="container py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Image
                  src="/asu-logo.png" // ← your file path in /public
                  alt="ASU"
                  width={240}
                  height={72}
                  className="h-15 w-auto"
                  priority
                />
                <div>
                  <h1 className="text-2xl font-bold text-asu-black">
                    ReQUESTA
                  </h1>
                  <p className="text-muted-foreground">
                    Academic Questions Generator
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <nav className="flex items-center gap-4">
                  <NavLink href="/about">About</NavLink>
                  <NavLink href="/faqs">FAQs</NavLink>
                </nav>
              </div>
            </div>
          </div>
        </header>
        <main className="container py-8">
          <div className="max-w-7xl mx-auto space-y-8">
            <HomeClient />
          </div>
        </main>
        <BlockingOverlay message="ReQUESTA is generating questions" />
      </OverlayProvider>
    </div>
  );
}
