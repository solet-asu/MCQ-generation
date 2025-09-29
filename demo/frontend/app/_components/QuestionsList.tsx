"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

import { Download, Eye, EyeOff, RotateCcw, Sparkles } from "lucide-react"

type Question = {
  id: number
  type: string
  question: string
  options: string[]
  correct: number // -1 if unknown
  explanation: string
  questionType?: string
}

type Props = {
  questions: Question[]
  totalQuestions?: number // optional: for empty state text
}

export default function QuestionsList({ questions, totalQuestions }: Props) {
  // local UI state – does not need to live in parent
  const [selectedAnswers, setSelectedAnswers] = useState<{ [id: number]: number }>({})
  const [revealedQuestions, setRevealedQuestions] = useState<{ [id: number]: boolean }>({})

  const [isDownloadModalOpen, setIsDownloadModalOpen] = useState(false)
  const [downloadFormat, setDownloadFormat] = useState("pdf")
  const [contentType, setContentType] = useState("questions-with-answers")
  const [includeAnswerKey, setIncludeAnswerKey] = useState(true)

  const toggleQuestionReveal = (qid: number) => {
    setRevealedQuestions((prev) => ({ ...prev, [qid]: !prev[qid] }))
  }

  const regenerateQuestion = (qid: number) => {
    // placeholder – hook to your per-question regenerate API later
    console.log(`Regenerating question ${qid}`)
  }

  const handleDownload = () => {
    const downloadOptions = {
      format: downloadFormat,
      contentType,
      includeAnswerKey,
      questionsCount: questions.length,
    }
    console.log("[v0] Download options:", downloadOptions)
    setIsDownloadModalOpen(false)
  }

  return (
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
                  <Button variant="outline" size="sm" className="flex items-center gap-2 bg-transparent cursor-pointer">
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
                    {/* Content type */}
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
                              Download just the questions and answer choices (no answers/explanations shown)
                            </p>
                          </div>
                        </div>

                        <div
                          className="flex items-start space-x-3 p-3 rounded-lg border border-gray-200 hover:bg-muted/30 cursor-pointer"
                          onClick={() => setContentType("questions-with-answers")}
                        >
                          <RadioGroupItem value="questions-with-answers" id="questions-with-answers" className="mt-0.5" />
                          <div className="flex-1">
                            <Label htmlFor="questions-with-answers" className="cursor-pointer font-medium text-sm">
                              Questions with Answers & Explanations
                            </Label>
                            <p className="text-xs text-muted-foreground mt-1">
                              Include correct answers highlighted and detailed explanations
                            </p>
                          </div>
                        </div>
                      </RadioGroup>
                    </div>

                    {/* Additional options */}
                    <div className="space-y-3">
                      <Label className="text-sm font-medium">Additional Options</Label>
                      <div className="space-y-2">
                        <div className="flex items-start space-x-3 p-3 rounded-lg border border-gray-200">
                          <input
                            id="include-answer-key"
                            type="checkbox"
                            checked={includeAnswerKey}
                            onChange={(e) => setIncludeAnswerKey(e.target.checked)}
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

                    {/* Format */}
                    <div className="space-y-3">
                      <Label className="text-sm font-medium">File Format</Label>
                      <RadioGroup value={downloadFormat} onValueChange={setDownloadFormat} className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="pdf" id="pdf" />
                          <Label htmlFor="pdf" className="cursor-pointer text-sm">
                            PDF Document (.pdf)
                          </Label>
                          <span className="text-xs text-muted-foreground ml-2">- Best for printing and sharing</span>
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
                      <Button variant="outline" onClick={() => setIsDownloadModalOpen(false)} className="cursor-pointer">
                        Cancel
                      </Button>
                      <Button onClick={handleDownload} className="bg-asu-maroon hover:bg-asu-maroon/90 text-white cursor-pointer">
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
                  Add your text and configure settings to generate questions{typeof totalQuestions === "number" ? ` (${totalQuestions} planned)` : ""}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {questions.map((q, index) => {
              const selected = selectedAnswers[q.id]
              const revealed = !!revealedQuestions[q.id]
              return (
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
                        title={revealed ? "Hide answer" : "Reveal answer"}
                      >
                        {revealed ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
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
                    {q.options.map((option, i) => {
                      let optionClasses =
                        "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors bg-white "
                      let circleClasses =
                        "w-6 h-6 rounded-full border-2 flex items-center justify-center text-sm font-medium flex-shrink-0 "
                      let textClasses = "leading-relaxed text-black "

                      if (revealed) {
                        if (i === q.correct) {
                          optionClasses += "border-[#78BE20]"
                          circleClasses += "bg-[#78BE20] text-white border-[#78BE20]"
                          textClasses += "font-medium"
                        } else if (selected === i) {
                          optionClasses += "border-red-500"
                          circleClasses += "bg-red-500 text-white border-red-500"
                        } else {
                          optionClasses += "border-border hover:bg-muted/50"
                          circleClasses += "border-border bg-white text-black"
                        }
                      } else {
                        if (selected === i) {
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

                  {revealed && (
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
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
