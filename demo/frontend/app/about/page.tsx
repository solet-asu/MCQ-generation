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
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-asu-maroon text-white">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-asu-maroon">
                    ReQUESTA
                  </h1>
                  <p className="text-muted-foreground">
                    Academic Question Generator
                  </p>
                </div>
              </div>
            </div>
            <Badge className="bg-asu-gold text-black font-medium">
              ASU Unity
            </Badge>
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
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Revolutionizing academic assessment through AI-powered question
                generation
              </p>
            </div>
          </div>

          {/* Mission Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-asu-maroon">
                <Target className="h-5 w-5" />
                Our Mission
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-lg">
                ReQUESTA empowers educators and students by transforming
                academic texts into high-quality, pedagogically sound
                multiple-choice questions using advanced artificial
                intelligence.
              </p>
              <p>
                Our platform bridges the gap between content creation and
                assessment, making it easier for educators to create meaningful
                evaluations while helping students engage more deeply with
                academic material through thoughtfully crafted questions.
              </p>
            </CardContent>
          </Card>

          {/* Features Grid */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-asu-maroon">
                  <FileText className="h-5 w-5" />
                  Smart Text Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Advanced AI algorithms analyze academic texts to identify key
                  concepts, relationships, and learning objectives for optimal
                  question generation.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-asu-maroon">
                  <Settings className="h-5 w-5" />
                  Customizable Settings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Configure question types, difficulty levels, and cognitive
                  complexity to match your specific educational goals and
                  assessment needs.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-asu-maroon">
                  <Lightbulb className="h-5 w-5" />
                  Multiple Question Types
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Generate text-based, inferential, and main idea questions that
                  test different levels of comprehension and critical thinking
                  skills.
                </p>
              </CardContent>
            </Card>
          </div>

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

          {/* Team Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-asu-maroon">
                <Users className="h-5 w-5" />
                Built at ASU
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                ReQUESTA is developed by Arizona State University as part of our
                commitment to innovation in education technology. Our
                interdisciplinary team combines expertise in artificial
                intelligence, educational psychology, and user experience
                design.
              </p>
              <div className="flex items-center gap-4 pt-4">
                <Badge className="bg-asu-gold text-black">ASU Innovation</Badge>
                <Badge variant="outline">Educational Technology</Badge>
                <Badge variant="outline">AI Research</Badge>
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
