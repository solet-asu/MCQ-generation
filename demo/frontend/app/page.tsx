"use client"

import type React from "react"
import Link from "next/link"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Upload,
  FileText,
  Settings,
  Sparkles,
  Download,
  Eye,
  EyeOff,
  RotateCcw,
  CheckCircle,
  Zap,
  Clock,
  Type,
  Info,
  HelpCircle,
} from "lucide-react"

export default function HomePage() {
  const [text, setText] = useState("")
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [inputMethod, setInputMethod] = useState("paste")

  // Question configuration
  const [textBasedQuestions, setTextBasedQuestions] = useState(5)
  const [inferentialQuestions, setInferentialQuestions] = useState(3)
  const [includeMainIdea, setIncludeMainIdea] = useState(true)
  const [selectedModel, setSelectedModel] = useState("gpt-4")
  const [qualityLevel, setQualityLevel] = useState("balanced")

  const [questions, setQuestions] = useState<any[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: number }>({})
  const [revealedQuestions, setRevealedQuestions] = useState<{ [key: number]: boolean }>({})

  // Download modal state
  const [isDownloadModalOpen, setIsDownloadModalOpen] = useState(false)
  const [downloadFormat, setDownloadFormat] = useState("pdf")
  const [contentType, setContentType] = useState("questions-with-answers") // questions-only or questions-with-answers
  const [includeAnswerKey, setIncludeAnswerKey] = useState(true)

  const totalQuestions = textBasedQuestions + inferentialQuestions + (includeMainIdea ? 1 : 0)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setUploadedFile(file)
      // Simulate file processing
      setText(
        `[Content from ${file.name}]\n\nThis is sample text extracted from the uploaded file. In a real implementation, this would be the actual content extracted from the PDF, DOC, or TXT file.`,
      )
    }
  }

  const handleGenerate = async () => {
    setIsGenerating(true)

    try {
      const requestPayload = {
        text: text,
        fact: textBasedQuestions,
        inference: inferentialQuestions,
        main_idea: includeMainIdea ? 1 : 0,
        quality_first: qualityLevel === "high" ? "yes" : "no",
      }

      console.log("[v0] API Request Payload:", requestPayload)

      const response = await fetch("https://damion-unframed-inez.ngrok-free.dev/generate_mcq", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestPayload),
      })

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`)
      }

      const apiData = await response.json()

      console.log("[v0] API Response Data:", apiData)

      let parsedQuestions = []

      // Check if the API response has the expected format
      if (Array.isArray(apiData) && apiData.length > 0 && apiData[0].mcq && apiData[0].mcq_answer) {
        // Expected format: array of {mcq: string, mcq_answer: string}
        parsedQuestions = apiData.map((item: any, index: number) => {
          return parseQuestionItem(item, index)
        })
      } else if (Array.isArray(apiData) && apiData.length > 0 && apiData[0].system_prompt) {
        // Handle the current API response format with system_prompt
        console.log("[v0] API returned system_prompt format, using fallback questions")
        throw new Error("API returned unexpected format")
      } else {
        // Unknown format
        console.log("[v0] API returned unknown format:", apiData)
        throw new Error("API returned unknown format")
      }

      setQuestions(parsedQuestions)
      setIsGenerating(false)

      setTimeout(() => {
        const questionsSection = document.querySelector("[data-questions-section]")
        if (questionsSection) {
          questionsSection.scrollIntoView({
            behavior: "smooth",
            block: "start",
          })
        }
      }, 300)
    } catch (error) {
      console.error("Error generating questions:", error)
      setIsGenerating(false)

      const sampleQuestions = [
        {
          id: 1,
          type: "Text-based",
          question: "According to the passage, what is the primary factor that influences student engagement?",
          options: [
            "The complexity of the material",
            "The teaching methodology used",
            "The student's prior knowledge",
            "The classroom environment",
          ],
          correct: 1,
          explanation:
            "Sample explanation - This will be provided by the API in future updates. The explanation will detail why this answer is correct and provide additional context from the source material.",
          questionType: "Sample type - This will categorize the cognitive level in future updates.",
        },
        {
          id: 2,
          type: "Inferential",
          question:
            "Based on the information provided, what can be inferred about the relationship between technology and learning outcomes?",
          options: [
            "Technology always improves learning outcomes",
            "Technology has no impact on learning",
            "Technology's impact depends on implementation",
            "Technology hinders traditional learning methods",
          ],
          correct: 2,
          explanation:
            "Sample explanation - This will be provided by the API in future updates. The explanation will detail why this answer is correct and provide additional context from the source material.",
          questionType: "Sample type - This will categorize the cognitive level in future updates.",
        },
      ]

      if (includeMainIdea) {
        sampleQuestions.push({
          id: 3,
          type: "Main Idea",
          question: "What is the central theme of this passage?",
          options: [
            "The importance of educational technology",
            "Factors affecting student learning and engagement",
            "Traditional vs modern teaching methods",
            "The role of teachers in student success",
          ],
          correct: 1,
          explanation:
            "Sample explanation - This will be provided by the API in future updates. The explanation will detail why this answer is correct and provide additional context from the source material.",
          questionType: "Sample type - This will categorize the cognitive level in future updates.",
        })
      }

      setQuestions(sampleQuestions)

      setTimeout(() => {
        const questionsSection = document.querySelector("[data-questions-section]")
        if (questionsSection) {
          questionsSection.scrollIntoView({
            behavior: "smooth",
            block: "start",
          })
        }
      }, 300)
    }
  }

  const toggleQuestionReveal = (questionId: number) => {
    setRevealedQuestions((prev) => ({
      ...prev,
      [questionId]: !prev[questionId],
    }))
  }

  const regenerateQuestion = (questionId: number) => {
    // In a real implementation, this would call the API to regenerate just this question
    console.log(`Regenerating question ${questionId}`)
  }

  const handleDownload = () => {
    const downloadOptions = {
      format: downloadFormat,
      contentType: contentType,
      includeAnswerKey: includeAnswerKey,
      questionsCount: questions.length,
    }

    console.log("[v0] Download initiated with options:", downloadOptions)

    // In a real implementation, this would generate and download the file based on the selected options
    if (contentType === "questions-only") {
      console.log("[v0] Generating file with questions only (no answers or explanations)")
    } else {
      console.log("[v0] Generating file with questions, answers, and explanations")
    }

    if (includeAnswerKey) {
      console.log("[v0] Including separate answer key section at the end")
    }

    console.log(`[v0] File format: ${downloadFormat.toUpperCase()}`)

    setIsDownloadModalOpen(false)
  }

  const canGenerate = (text.trim().length > 50 || uploadedFile) && totalQuestions > 0

  const parseQuestionItem = (item: any, index: number) => {
    const mcqText = item.mcq
    const correctAnswer = item.mcq_answer

    console.log(`[v0] Parsing question ${index + 1}:`)
    console.log(`[v0] MCQ Text: "${mcqText}"`)
    console.log(`[v0] Correct Answer: "${correctAnswer}"`)

    // More robust question extraction
    let question = ""
    let options: string[] = []

    // Try to extract question and options using multiple approaches
    // Method 1: Split by A), B), C), D) patterns
    const parts = mcqText.split(/\s*[A-D]\)\s*/)
    if (parts.length >= 2) {
      question = parts[0].trim()
      // Take the next parts as options, filtering out empty ones
      for (let i = 1; i < parts.length && options.length < 4; i++) {
        const option = parts[i].trim()
        if (option) {
          options.push(option)
        }
      }
    }

    // Method 2: If first method didn't work, try regex approach
    if (options.length === 0) {
      const questionMatch = mcqText.match(/^(.*?)(?=\s*[A-D]\))/s)
      if (questionMatch) {
        question = questionMatch[1].trim()
      }

      const optionMatches = mcqText.match(/[A-D]\)\s*([^A-D]*?)(?=\s*[A-D]\)|$)/gs)
      if (optionMatches) {
        options = optionMatches
          .map((match) => match.replace(/^[A-D]\)\s*/, "").trim())
          .filter((option) => option.length > 0)
      }
    }

    if (question) {
      // Remove patterns like "Q1:", "Q2:", "Question 1:", etc. from the beginning
      question = question.replace(/^(?:Q\d+:|Question\s+\d+:)\s*/i, "").trim()
    }

    // Fallback if parsing failed
    if (!question || options.length === 0) {
      question = mcqText
      options = ["Option A", "Option B", "Option C", "Option D"]
    }

    console.log(`[v0] Parsed question: "${question}"`)
    console.log(`[v0] Parsed options:`, options)

    let correctIndex = -1

    if (correctAnswer) {
      const answerText = correctAnswer.trim()

      // Format 1: Plain letter (A, B, C, D)
      const letterMatch = answerText.match(/^([A-D])\b/)
      if (letterMatch) {
        correctIndex = letterMatch[1].charCodeAt(0) - 65
        console.log(`[v0] Found plain letter format: ${letterMatch[1]} -> index ${correctIndex}`)
      }

      // Format 2: Letter with closing parenthesis (A), B), etc.)
      if (correctIndex === -1) {
        const parenMatch = answerText.match(/^([A-D])\)/)
        if (parenMatch) {
          correctIndex = parenMatch[1].charCodeAt(0) - 65
          console.log(`[v0] Found closing paren format: ${parenMatch[1]}) -> index ${correctIndex}`)
        }
      }

      // Format 3: Letter with parentheses ((A), (B), etc.)
      if (correctIndex === -1) {
        const fullParenMatch = answerText.match(/$$([A-D])$$/)
        if (fullParenMatch) {
          correctIndex = fullParenMatch[1].charCodeAt(0) - 65
          console.log(`[v0] Found full paren format: (${fullParenMatch[1]}) -> index ${correctIndex}`)
        }
      }

      // Format 4: "Answer: X" format
      if (correctIndex === -1) {
        const answerPrefixMatch = answerText.match(/Answer:\s*([A-D])/i)
        if (answerPrefixMatch) {
          correctIndex = answerPrefixMatch[1].toUpperCase().charCodeAt(0) - 65
          console.log(`[v0] Found answer prefix format: Answer: ${answerPrefixMatch[1]} -> index ${correctIndex}`)
        }
      }

      // Format 5: Direct text comparison with options (normalize case and whitespace)
      if (correctIndex === -1) {
        const normalizedAnswer = answerText.toLowerCase().trim()
        for (let i = 0; i < options.length; i++) {
          const normalizedOption = options[i].toLowerCase().trim()
          if (normalizedOption === normalizedAnswer) {
            correctIndex = i
            console.log(`[v0] Found direct text match: "${answerText}" matches option ${i}: "${options[i]}"`)
            break
          }
        }
      }

      // Format 6: Partial text match (in case the answer contains part of the option)
      if (correctIndex === -1) {
        const normalizedAnswer = answerText.toLowerCase().trim()
        for (let i = 0; i < options.length; i++) {
          const normalizedOption = options[i].toLowerCase().trim()
          if (normalizedOption.includes(normalizedAnswer) || normalizedAnswer.includes(normalizedOption)) {
            correctIndex = i
            console.log(`[v0] Found partial text match: "${answerText}" partially matches option ${i}: "${options[i]}"`)
            break
          }
        }
      }
    }

    if (correctIndex === -1) {
      console.log(`[v0] WARNING: Could not parse correct answer for question ${index + 1}: "${correctAnswer}"`)
      console.log(`[v0] Available options:`, options)
      // Don't default to A - leave as -1 to indicate parsing failure
      correctIndex = -1
    } else {
      console.log(`[v0] Final correct index: ${correctIndex} (${String.fromCharCode(65 + correctIndex)})`)
    }

    // Determine question type based on index and settings
    let questionType = "Text-based"
    if (index < textBasedQuestions) {
      questionType = "Text-based"
    } else if (index < textBasedQuestions + inferentialQuestions) {
      questionType = "Inferential"
    } else {
      questionType = "Main Idea"
    }

    return {
      id: index + 1,
      type: questionType,
      question: question,
      options: options,
      correct: correctIndex, // Keep -1 if parsing failed instead of defaulting to 0
      explanation:
        "Sample explanation - This will be provided by the API in future updates. The explanation will detail why this answer is correct and provide additional context from the source material.",
      questionType:
        "Sample type - This will categorize the cognitive level (Remember, Understand, Apply, Analyze, Evaluate, Create) in future updates.",
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {isGenerating && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center space-y-8">
            <div className="relative">
              <div className="w-32 h-32 mx-auto relative">
                {/* Outer rotating ring - simplified to white */}
                <div className="absolute inset-0 border-4 border-white/30 rounded-full animate-spin"></div>
                {/* Inner pulsing circle - simplified to white */}
                <div className="absolute inset-4 bg-white/10 rounded-full animate-pulse"></div>
                {/* Center brain icon - white */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <Sparkles className="w-12 h-12 text-white animate-pulse" />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white">ReQUESTA is generating questions</h2>
              <div className="flex items-center justify-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: "0s" }}></div>
                  <div
                    className="w-2 h-2 bg-white rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-white rounded-full animate-bounce"
                    style={{ animationDelay: "0.4s" }}
                  ></div>
                </div>
              </div>
              <p className="text-white/80 max-w-md mx-auto">
                Our AI is analyzing your text and crafting {totalQuestions} thoughtful questions...
              </p>
            </div>
          </div>
        </div>
      )}

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
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Text Input Section - Takes 2/3 of the width */}
            <div className="lg:col-span-2">
              <Card className="h-full">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-asu-maroon">
                    <FileText className="h-5 w-5" />
                    Input Academic Text
                  </CardTitle>
                  <CardDescription>
                    Choose how you want to input your academic text for question generation
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 h-full flex flex-col">
                  <Tabs value={inputMethod} onValueChange={setInputMethod} className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="paste" className="flex items-center gap-2">
                        <Type className="h-4 w-4" />
                        Paste Text
                      </TabsTrigger>
                      <TabsTrigger value="upload" className="flex items-center gap-2">
                        <Upload className="h-4 w-4" />
                        Upload File
                      </TabsTrigger>
                    </TabsList>

                    <TabsContent value="paste" className="space-y-4 flex-1 flex flex-col">
                      <div className="space-y-2 flex-1">
                        <Label htmlFor="text-input">Academic Text</Label>
                        <Textarea
                          id="text-input"
                          placeholder="Paste your academic text here..."
                          value={text}
                          onChange={(e) => setText(e.target.value)}
                          className="min-h-[350px] resize-none flex-1 custom-textarea"
                        />
                        <div className="flex items-center justify-between text-sm text-muted-foreground">
                          <span>{text.length} characters</span>
                          <span>{text.split(/\s+/).filter(Boolean).length} words</span>
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="upload" className="space-y-4 flex-1 flex flex-col">
                      <div className="space-y-4 flex-1">
                        <Label>Upload Document</Label>
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                          <input
                            type="file"
                            id="file-upload"
                            accept=".pdf,.doc,.docx,.txt"
                            onChange={handleFileUpload}
                            className="hidden"
                          />
                          <div className="space-y-4">
                            <div className="w-16 h-16 mx-auto bg-muted rounded-full flex items-center justify-center">
                              <Upload className="h-8 w-8 text-muted-foreground" />
                            </div>
                            <div>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => document.getElementById("file-upload")?.click()}
                                className="mb-2 cursor-pointer"
                              >
                                Choose File
                              </Button>
                              <p className="text-sm text-muted-foreground">PDF, DOC, DOCX, TXT files supported</p>
                            </div>
                          </div>
                        </div>
                        {uploadedFile && (
                          <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
                            <FileText className="h-4 w-4" />
                            <span className="text-sm font-medium">{uploadedFile.name}</span>
                            <Badge variant="secondary" className="ml-auto">
                              Uploaded
                            </Badge>
                          </div>
                        )}
                        {text && (
                          <div className="mt-4">
                            <Label>Extracted Text Preview</Label>
                            <div className="mt-2 p-3 bg-muted rounded-lg max-h-32 overflow-y-auto text-sm">
                              {text.substring(0, 200)}...
                            </div>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                  </Tabs>

                  <div className="bg-muted/30 rounded-lg p-4 space-y-2">
                    <h4 className="text-sm font-medium text-asu-maroon">Tips for Better Questions:</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li className="flex items-start gap-2">
                        <span className="text-asu-gold">•</span>
                        <span>Ensure your text is at least 100 words for optimal question generation</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-asu-gold">•</span>
                        <span>Include clear concepts, definitions, and examples in your text</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-asu-gold">•</span>
                        <span>Academic papers, textbook chapters, and research articles work best</span>
                      </li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Configuration Section - Takes 1/3 of the width */}
            <div className="lg:col-span-1">
              <Card className="h-full">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-asu-maroon">
                    <Settings className="h-5 w-5" />
                    Configuration
                  </CardTitle>
                  <CardDescription>Customize your question settings</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 h-full flex flex-col">
                  <div className="space-y-4 flex-1">
                    <div className="space-y-3">
                      <h3 className="font-medium text-sm">Question Types</h3>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label htmlFor="text-based" className="text-sm">
                            Text-based
                          </Label>
                          <Input
                            id="text-based"
                            type="number"
                            min="0"
                            value={textBasedQuestions}
                            onChange={(e) => setTextBasedQuestions(Math.max(0, Number.parseInt(e.target.value) || 0))}
                            className="w-16 h-8 custom-input"
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">Questions directly answered from the text</p>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label htmlFor="inferential" className="text-sm">
                            Inferential
                          </Label>
                          <Input
                            id="inferential"
                            type="number"
                            min="0"
                            value={inferentialQuestions}
                            onChange={(e) => setInferentialQuestions(Math.max(0, Number.parseInt(e.target.value) || 0))}
                            className="w-16 h-8 custom-input"
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">Questions requiring analysis beyond the text</p>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="main-idea"
                            checked={includeMainIdea}
                            onCheckedChange={(checked) => setIncludeMainIdea(checked as boolean)}
                          />
                          <Label htmlFor="main-idea" className="text-sm">
                            Main Idea Question
                          </Label>
                        </div>
                        <p className="text-xs text-muted-foreground ml-6">One question about the central theme</p>
                      </div>
                    </div>

                    <div className="space-y-3 pt-3 border-t border-border">
                      <h3 className="font-medium text-sm">Settings</h3>

                      <div className="space-y-2">
                        <Label className="text-sm">AI Model</Label>
                        <Select value={selectedModel} onValueChange={setSelectedModel}>
                          <SelectTrigger className="h-8 custom-input">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="gpt-4">GPT-4</SelectItem>
                            <SelectItem value="gpt-3.5">GPT-3.5</SelectItem>
                            <SelectItem value="claude">Claude</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-sm">Quality & Speed</Label>
                        <RadioGroup value={qualityLevel} onValueChange={setQualityLevel} className="space-y-1">
                          <div
                            className="flex items-center space-x-2 p-2 rounded border border-gray-300 hover:bg-muted/50 cursor-pointer"
                            onClick={() => setQualityLevel("high")}
                          >
                            <RadioGroupItem value="high" id="high" />
                            <div className="flex-1">
                              <Label htmlFor="high" className="flex items-center gap-2 cursor-pointer text-sm">
                                <CheckCircle className="h-3 w-3 text-gray-600" />
                                <span>High Quality</span>
                              </Label>
                              <p className="text-xs text-muted-foreground">Best accuracy, slower</p>
                            </div>
                          </div>
                          <div
                            className="flex items-center space-x-2 p-2 rounded border border-gray-300 hover:bg-muted/50 cursor-pointer"
                            onClick={() => setQualityLevel("fast")}
                          >
                            <RadioGroupItem value="fast" id="fast" />
                            <div className="flex-1">
                              <Label htmlFor="fast" className="flex items-center gap-2 cursor-pointer text-sm">
                                <Zap className="h-3 w-3 text-gray-600" />
                                <span>Fast Generation</span>
                              </Label>
                              <p className="text-xs text-muted-foreground">Quick results, good quality</p>
                            </div>
                          </div>
                        </RadioGroup>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-border space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Total Questions:</span>
                        <Badge className="bg-asu-gold text-black">{totalQuestions}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Est. Time:</span>
                        <span className="text-sm flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {Math.ceil(totalQuestions * (qualityLevel === "high" ? 1 : 0.5))} min
                        </span>
                      </div>
                    </div>
                  </div>

                  <Button
                    onClick={handleGenerate}
                    disabled={!canGenerate || isGenerating}
                    className="w-full min-w-[112px] px-8 py-3 bg-asu-gold hover:bg-asu-gold/90 text-black font-medium rounded-full transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 cursor-pointer"
                    size="lg"
                  >
                    {isGenerating ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-black mr-2" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        Generate {totalQuestions}
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>

          <div className="w-full" data-questions-section>
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-asu-maroon">Generated Questions</CardTitle>
                    <CardDescription>
                      {questions.length > 0
                        ? `${questions.length} questions generated successfully`
                        : "Questions will appear here after generation"}
                    </CardDescription>
                  </div>
                  {questions.length > 0 && (
                    <div className="flex items-center gap-2">
                      <Dialog open={isDownloadModalOpen} onOpenChange={setIsDownloadModalOpen}>
                        <DialogTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex items-center gap-2 bg-transparent cursor-pointer"
                          >
                            <Download className="h-4 w-4" />
                            Download
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-lg">
                          <DialogHeader>
                            <DialogTitle>Download Questions</DialogTitle>
                            <DialogDescription>Choose your download format and content options</DialogDescription>
                          </DialogHeader>
                          <div className="space-y-6">
                            <div className="space-y-3">
                              <Label className="text-sm font-medium">Content Type</Label>
                              <RadioGroup value={contentType} onValueChange={setContentType} className="space-y-3">
                                <div
                                  className="flex items-start space-x-3 p-3 rounded-lg border border-gray-200 hover:bg-muted/30 cursor-pointer"
                                  onClick={() => setContentType("questions-only")}
                                >
                                  <RadioGroupItem value="questions-only" id="questions-only" className="mt-0.5" />
                                  <div className="flex-1">
                                    <Label htmlFor="questions-only" className="cursor-pointer font-medium text-sm">
                                      Questions Only
                                    </Label>
                                    <p className="text-xs text-muted-foreground mt-1">
                                      Download just the questions and answer choices (no correct answers or explanations
                                      shown)
                                    </p>
                                  </div>
                                </div>
                                <div
                                  className="flex items-start space-x-3 p-3 rounded-lg border border-gray-200 hover:bg-muted/30 cursor-pointer"
                                  onClick={() => setContentType("questions-with-answers")}
                                >
                                  <RadioGroupItem
                                    value="questions-with-answers"
                                    id="questions-with-answers"
                                    className="mt-0.5"
                                  />
                                  <div className="flex-1">
                                    <Label
                                      htmlFor="questions-with-answers"
                                      className="cursor-pointer font-medium text-sm"
                                    >
                                      Questions with Answers & Explanations
                                    </Label>
                                    <p className="text-xs text-muted-foreground mt-1">
                                      Download questions with correct answers highlighted and detailed explanations
                                      included
                                    </p>
                                  </div>
                                </div>
                              </RadioGroup>
                            </div>

                            <div className="space-y-3">
                              <Label className="text-sm font-medium">Additional Options</Label>
                              <div className="space-y-2">
                                <div className="flex items-start space-x-3 p-3 rounded-lg border border-gray-200">
                                  <Checkbox
                                    id="include-answer-key"
                                    checked={includeAnswerKey}
                                    onCheckedChange={(checked) => setIncludeAnswerKey(checked as boolean)}
                                    className="mt-0.5"
                                  />
                                  <div className="flex-1">
                                    <Label htmlFor="include-answer-key" className="cursor-pointer font-medium text-sm">
                                      Include Answer Key at End
                                    </Label>
                                    <p className="text-xs text-muted-foreground mt-1">
                                      Add a separate answer key section at the end of the document (useful for teachers)
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div className="space-y-3">
                              <Label className="text-sm font-medium">File Format</Label>
                              <RadioGroup
                                value={downloadFormat}
                                onValueChange={setDownloadFormat}
                                className="space-y-2"
                              >
                                <div className="flex items-center space-x-2">
                                  <RadioGroupItem value="pdf" id="pdf" />
                                  <Label htmlFor="pdf" className="cursor-pointer text-sm">
                                    PDF Document (.pdf)
                                  </Label>
                                  <span className="text-xs text-muted-foreground ml-2">
                                    - Best for printing and sharing
                                  </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <RadioGroupItem value="docx" id="docx" />
                                  <Label htmlFor="docx" className="cursor-pointer text-sm">
                                    Word Document (.docx)
                                  </Label>
                                  <span className="text-xs text-muted-foreground ml-2">- Editable format</span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <RadioGroupItem value="txt" id="txt" />
                                  <Label htmlFor="txt" className="cursor-pointer text-sm">
                                    Plain Text (.txt)
                                  </Label>
                                  <span className="text-xs text-muted-foreground ml-2">- Simple, universal format</span>
                                </div>
                              </RadioGroup>
                            </div>

                            <div className="flex justify-end gap-3 pt-4 border-t border-border">
                              <Button
                                variant="outline"
                                onClick={() => setIsDownloadModalOpen(false)}
                                className="cursor-pointer"
                              >
                                Cancel
                              </Button>
                              <Button
                                onClick={handleDownload}
                                className="bg-asu-maroon hover:bg-asu-maroon/90 text-white cursor-pointer"
                              >
                                <Download className="h-4 w-4 mr-2" />
                                Download {downloadFormat.toUpperCase()}
                              </Button>
                            </div>
                          </div>
                        </DialogContent>
                      </Dialog>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {questions.length === 0 ? (
                  <div className="flex items-center justify-center h-96 text-center">
                    <div className="space-y-4">
                      <div className="w-16 h-16 mx-auto bg-muted rounded-full flex items-center justify-center">
                        <Sparkles className="h-8 w-8 text-muted-foreground" />
                      </div>
                      <div>
                        <h3 className="font-medium text-muted-foreground">No questions generated yet</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          Add your text and configure settings to generate questions
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Changed from grid to vertical stack for row-by-row display */
                  <div className="space-y-6">
                    {questions.map((q, index) => (
                      <div key={q.id} className="border border-border rounded-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-foreground">Question {index + 1}</span>
                            <Badge className="bg-[#E8E8E8] text-black font-medium pointer-events-none cursor-default">
                              {q.type}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleQuestionReveal(q.id)}
                              className="h-8 w-8 p-0 cursor-pointer"
                              title={revealedQuestions[q.id] ? "Hide answer" : "Reveal answer"}
                            >
                              {revealedQuestions[q.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => regenerateQuestion(q.id)}
                              className="h-8 w-8 p-0 cursor-pointer"
                              title="Regenerate this question"
                            >
                              <RotateCcw className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>

                        <h3 className="font-medium mb-4 text-lg leading-tight">{q.question}</h3>

                        <div className="space-y-3">
                          {q.options.map((option: string, i: number) => {
                            let optionClasses =
                              "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors bg-white "
                            let circleClasses =
                              "w-6 h-6 rounded-full border-2 flex items-center justify-center text-sm font-medium flex-shrink-0 "
                            let textClasses = "leading-relaxed text-black "

                            if (revealedQuestions[q.id]) {
                              // When revealed, show correct answer in ASU green, wrong selected answer in red
                              if (i === q.correct) {
                                optionClasses += "border-[#78BE20]"
                                circleClasses += "bg-[#78BE20] text-white border-[#78BE20]"
                                textClasses += "font-medium"
                              } else if (selectedAnswers[q.id] === i) {
                                optionClasses += "border-red-500"
                                circleClasses += "bg-red-500 text-white border-red-500"
                              } else {
                                optionClasses += "border-border hover:bg-muted/50"
                                circleClasses += "border-border bg-white text-black"
                              }
                            } else {
                              // When not revealed, show selected answer with neutral gray border and circle
                              if (selectedAnswers[q.id] === i) {
                                optionClasses += "border-gray-400"
                                circleClasses += "bg-gray-600 text-white border-gray-600"
                              } else {
                                optionClasses += "border-border hover:bg-muted/50"
                                circleClasses += "border-border bg-white text-black"
                              }
                            }

                            return (
                              <div
                                key={i}
                                className={optionClasses + " cursor-pointer"}
                                onClick={() => setSelectedAnswers((prev) => ({ ...prev, [q.id]: i }))}
                              >
                                <div className={circleClasses}>{String.fromCharCode(65 + i)}</div>
                                <span className={textClasses}>{option}</span>
                              </div>
                            )
                          })}
                        </div>

                        {revealedQuestions[q.id] && (
                          <div className="mt-6 pt-4 border-t border-border">
                            <div className="bg-muted/50 rounded-lg p-4">
                              <p className="text-sm">
                                <strong className="text-foreground">Explanation:</strong>{" "}
                                <span className="text-muted-foreground">{q.explanation}</span>
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
