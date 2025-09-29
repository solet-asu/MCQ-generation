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
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Sparkles, HelpCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function FAQsPage() {
  const faqs = [
    {
      id: "what-is-requesta",
      question: "What is ReQUESTA?",
      answer:
        "ReQUESTA is an AI-powered academic question generator developed by Arizona State University. It transforms academic texts into high-quality multiple-choice questions, helping educators create assessments and students engage more deeply with learning materials.",
    },
    {
      id: "how-does-it-work",
      question: "How does ReQUESTA generate questions?",
      answer:
        "ReQUESTA uses advanced artificial intelligence algorithms to analyze your academic text, identify key concepts and relationships, and generate pedagogically sound multiple-choice questions. The AI considers different cognitive levels and question types to create comprehensive assessments.",
    },
    {
      id: "question-types",
      question: "What types of questions can ReQUESTA generate?",
      answer:
        "ReQUESTA can generate three main types of questions: Text-based questions (directly answered from the content), Inferential questions (requiring analysis and critical thinking), and Main Idea questions (focusing on central themes and concepts).",
    },
    {
      id: "supported-formats",
      question: "What file formats does ReQUESTA support?",
      answer:
        "You can input text by pasting directly into the platform or by uploading files in PDF, DOC, DOCX, or TXT formats. The system will automatically extract and process the text content from these documents.",
    },
    {
      id: "question-quality",
      question: "How can I ensure high-quality questions?",
      answer:
        "For best results, use academic texts that are at least 100 words long with clear concepts, definitions, and examples. Academic papers, textbook chapters, and research articles work particularly well. You can also adjust the quality settings to prioritize accuracy over speed.",
    },
    {
      id: "customization",
      question: "Can I customize the number and types of questions?",
      answer:
        "Yes! You can specify exactly how many text-based and inferential questions you want, choose whether to include a main idea question, select your preferred AI model, and adjust quality vs. speed preferences to match your needs.",
    },
    {
      id: "download-options",
      question: "What download options are available?",
      answer:
        "You can download your questions in PDF, Word (DOCX), or plain text (TXT) formats. You can choose to download questions only, or include answers and explanations. There's also an option to include a separate answer key section.",
    },
    {
      id: "text-length",
      question: "What's the ideal length for input text?",
      answer:
        "While ReQUESTA can work with shorter texts, we recommend using content that's at least 100-200 words for optimal question generation. Longer, more detailed texts typically produce better and more varied questions.",
    },
    {
      id: "accuracy",
      question: "How accurate are the generated questions?",
      answer:
        "ReQUESTA uses state-of-the-art AI models to ensure high accuracy. However, we recommend reviewing generated questions before use, especially for high-stakes assessments. The platform includes tools to regenerate individual questions if needed.",
    },
    {
      id: "educational-levels",
      question: "What educational levels does ReQUESTA support?",
      answer:
        "ReQUESTA is designed for academic content and works well for high school through graduate-level materials. The AI adapts to the complexity and style of your input text to generate appropriately challenging questions.",
    },
    {
      id: "privacy-security",
      question: "Is my content secure and private?",
      answer:
        "Yes, ReQUESTA takes privacy seriously. Your uploaded content is processed securely and is not stored permanently on our servers. We follow ASU's strict data privacy and security guidelines to protect your academic materials.",
    },
    {
      id: "technical-support",
      question: "What if I encounter technical issues?",
      answer:
        "If you experience any technical problems or have questions about using ReQUESTA, you can contact ASU's technical support team. We're committed to providing a smooth experience for all users.",
    },
    {
      id: "cost",
      question: "Is ReQUESTA free to use?",
      answer:
        "ReQUESTA is currently available as part of ASU's educational technology initiatives. Specific pricing and access details may vary depending on your affiliation with ASU or partner institutions.",
    },
    {
      id: "future-features",
      question: "What new features are planned?",
      answer:
        "We're continuously improving ReQUESTA based on user feedback. Planned features include support for additional question types, enhanced customization options, integration with learning management systems, and improved AI models for even better question quality.",
    },
  ];

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
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <div className="flex items-center justify-center gap-2 mb-4">
              <HelpCircle className="h-8 w-8 text-asu-maroon" />
            </div>
            <h1 className="text-4xl font-bold text-asu-maroon">
              Frequently Asked Questions
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Find answers to common questions about ReQUESTA and how to get the
              most out of our AI-powered question generator
            </p>
          </div>

          {/* Quick Links */}
          <Card>
            <CardHeader>
              <CardTitle className="text-asu-maroon">
                Quick Navigation
              </CardTitle>
              <CardDescription>
                Jump to the most commonly asked questions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                <Button
                  variant="ghost"
                  size="sm"
                  className="justify-start h-auto p-2 text-left"
                >
                  <a href="#what-is-requesta" className="text-sm">
                    What is ReQUESTA?
                  </a>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="justify-start h-auto p-2 text-left"
                >
                  <a href="#how-does-it-work" className="text-sm">
                    How does it work?
                  </a>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="justify-start h-auto p-2 text-left"
                >
                  <a href="#question-types" className="text-sm">
                    Question types
                  </a>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="justify-start h-auto p-2 text-left"
                >
                  <a href="#supported-formats" className="text-sm">
                    Supported formats
                  </a>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="justify-start h-auto p-2 text-left"
                >
                  <a href="#download-options" className="text-sm">
                    Download options
                  </a>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="justify-start h-auto p-2 text-left"
                >
                  <a href="#privacy-security" className="text-sm">
                    Privacy & Security
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* FAQ Accordion */}
          <Card>
            <CardHeader>
              <CardTitle className="text-asu-maroon">All Questions</CardTitle>
              <CardDescription>
                Browse through all frequently asked questions about ReQUESTA
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                {faqs.map((faq) => (
                  <AccordionItem key={faq.id} value={faq.id} id={faq.id}>
                    <AccordionTrigger className="text-left hover:text-asu-maroon">
                      {faq.question}
                    </AccordionTrigger>
                    <AccordionContent className="text-muted-foreground leading-relaxed">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>

          {/* Contact Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-asu-maroon">
                Still Have Questions?
              </CardTitle>
              <CardDescription>
                Can't find what you're looking for? We're here to help!
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/" className="flex-1">
                  <Button className="w-full bg-asu-maroon hover:bg-asu-maroon/90 text-white">
                    <Sparkles className="h-4 w-4 mr-2" />
                    Try ReQUESTA Now
                  </Button>
                </Link>
                <Link href="/about" className="flex-1">
                  <Button variant="outline" className="w-full bg-transparent">
                    Learn More About ReQUESTA
                  </Button>
                </Link>
              </div>
              <div className="mt-4 p-4 bg-muted/30 rounded-lg">
                <p className="text-sm text-muted-foreground text-center">
                  For technical support or additional questions, please contact
                  the ASU support team
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
