import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  FileText,
  Settings,
  Users,
  Target,
  Lightbulb,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="container py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button
                  variant="ghost"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to Generator
                </Button>
              </Link>
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
            </div>
          </div>
        </div>
      </header>

      <main className="container py-12">
        <div className="max-w-4xl mx-auto space-y-12">
          {/* Hero Section */}
          <div className="text-center space-y-6">
            <div className="space-y-4">
              <h1 className="text-4xl font-bold text-asu-maroon">
                About ReQUESTA
              </h1>
            </div>
          </div>

          {/* Mission Section */}
          <Card>
            <CardHeader></CardHeader>
            <CardContent className="space-y-4">
              <p className="text-md">
                ReQUESTA is a multi-agent workflow that turns long academic
                texts into high-quality, cognitively diverse multiple-choice
                questions. Instead of producing easy recall items, ReQUESTA
                plans around the source content’s key concepts and inferences,
                then crafts text-based, inferential, and main-idea questions
                that demand interpretation and synthesis. By ensuring plausible
                distractors and consistent quality checks, it yields questions
                that actually measure understanding. For educators, this means
                faster creation of valid assessments and richer practice items
                that reinforce what matters—not trivia. For learning systems and
                students, it powers self-assessment that builds metacognition:
                learners test themselves on central arguments and relationships,
                get meaningful feedback, and close gaps more effectively. In
                short, ReQUESTA turns long texts into targeted, high-quality
                MCQs that enhance teaching and deepen learning
              </p>
            </CardContent>
          </Card>

          {/* How It Works */}
          <Card>
            <CardHeader>
              <CardTitle className="text-asu-maroon">
                How ReQUESTA Works
              </CardTitle>
              <CardDescription>
                Our streamlined process makes question generation simple and
                effective
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-3">
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 mx-auto bg-asu-maroon text-white rounded-full flex items-center justify-center font-bold">
                    1
                  </div>
                  <h3 className="font-semibold">Input Your Text</h3>
                  <p className="text-sm text-muted-foreground">
                    Upload documents or paste academic content directly into the
                    platform
                  </p>
                </div>
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 mx-auto bg-asu-maroon text-white rounded-full flex items-center justify-center font-bold">
                    2
                  </div>
                  <h3 className="font-semibold">Configure Settings</h3>
                  <p className="text-sm text-muted-foreground">
                    Choose question types, quantities, and quality preferences
                  </p>
                </div>
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 mx-auto bg-asu-maroon text-white rounded-full flex items-center justify-center font-bold">
                    3
                  </div>
                  <h3 className="font-semibold">Generate & Export</h3>
                  <p className="text-sm text-muted-foreground">
                    Review AI-generated questions and export in your preferred
                    format
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Contact Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-asu-maroon">Get Started</CardTitle>
              <CardDescription>
                Ready to transform your academic content into engaging
                questions?
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/" className="flex-1">
                  <Button className="w-full bg-asu-maroon hover:bg-asu-maroon/90 text-white">
                    <Sparkles className="h-4 w-4 mr-2" />
                    Start Generating Questions
                  </Button>
                </Link>
                <Link href="/faqs" className="flex-1">
                  <Button variant="outline" className="w-full bg-transparent">
                    View FAQs
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
