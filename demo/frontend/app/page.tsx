import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Sparkles, Info, HelpCircle } from "lucide-react"
import HomeClient from "./_components/HomeClient"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="container py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-asu-maroon text-white">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-asu-maroon">ReQUESTA</h1>
                <p className="text-muted-foreground">Academic Question Generator</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <nav className="flex items-center gap-2">
                <Link href="/about">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex items-center gap-2 text-muted-foreground hover:text-asu-maroon"
                  >
                    <Info className="h-4 w-4" />
                    About
                  </Button>
                </Link>
                <Link href="/faqs">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex items-center gap-2 text-muted-foreground hover:text-asu-maroon"
                  >
                    <HelpCircle className="h-4 w-4" />
                    FAQs
                  </Button>
                </Link>
              </nav>
              <Badge className="bg-asu-gold text-black font-medium">ASU Unity</Badge>
            </div>
          </div>
        </div>
      </header>

      <main className="container py-8">
        <div className="max-w-7xl mx-auto space-y-8">
          <HomeClient />
        </div>
      </main>
    </div>
  )
}
