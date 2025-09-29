"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, Settings, Sparkles } from "lucide-react"

import UploadPanel from "./UploadPanel"
import ConfigPanel from "./ConfigPanel"
import dynamic from "next/dynamic"
import { useOverlay } from "./overlay-store"



const QuestionsList = dynamic(() => import("./QuestionsList"), {
  ssr: false,
  loading: () => <div className="text-sm text-muted-foreground">Loading questions…</div>,
})

type Question = {
  id: number
  type: string
  question: string
  options: string[]
  correct: number // -1 if unknown
  explanation: string
  questionType?: string
}

export default function HomeClient() {
  // input state
  const [text, setText] = useState("")
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [inputMethod, setInputMethod] = useState("paste")

  const { show, hide } = useOverlay()

  

  // config state
  const [textBasedQuestions, setTextBasedQuestions] = useState(5)
  const [inferentialQuestions, setInferentialQuestions] = useState(3)
  const [includeMainIdea, setIncludeMainIdea] = useState(true)
  const [selectedModel, setSelectedModel] = useState("gpt-4")
  const [qualityLevel, setQualityLevel] = useState("balanced")

  // generation state
  const [questions, setQuestions] = useState<Question[]>([])
  const [isGenerating, setIsGenerating] = useState(false)

  const totalQuestions = textBasedQuestions + inferentialQuestions + (includeMainIdea ? 1 : 0)
  const canGenerate = (text.trim().length > 50 || !!uploadedFile) && totalQuestions > 0

  const handleGenerate = async () => {
    show()
    setIsGenerating(true)
    try {
      const requestPayload = {
        text: text,
        fact: textBasedQuestions,
        inference: inferentialQuestions,
        main_idea: includeMainIdea ? 1 : 0,
        quality_first: qualityLevel === "high" ? "yes" : "no",
      }

      // call your API
      const response = await fetch("https://damion-unframed-inez.ngrok-free.dev/generate_mcq", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload),
      })
      if (!response.ok) throw new Error(`API request failed: ${response.status}`)

      const apiData = await response.json()

      let parsedQuestions: Question[] = []
      if (Array.isArray(apiData) && apiData.length > 0 && apiData[0].mcq && apiData[0].mcq_answer) {
        parsedQuestions = apiData.map((item: any, index: number) => parseQuestionItem(item, index))
      } else if (Array.isArray(apiData) && apiData.length > 0 && apiData[0].system_prompt) {
        throw new Error("API returned unexpected format")
      } else {
        throw new Error("API returned unknown format")
      }

      setQuestions(parsedQuestions)
      setIsGenerating(false)
      hide()

      // scroll to questions
      setTimeout(() => {
        const el = document.querySelector("[data-questions-section]")
        el?.scrollIntoView({ behavior: "smooth", block: "start" })
      }, 300)
    } catch (err) {
      console.error("Error generating questions:", err)
      setIsGenerating(false)

      // fallback sample questions
      const sample: Question[] = [
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
        sample.push({
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
      setQuestions(sample)

      setTimeout(() => {
        const el = document.querySelector("[data-questions-section]")
        el?.scrollIntoView({ behavior: "smooth", block: "start" })
      }, 300)
    }
  }

  const parseQuestionItem = (item: any, index: number): Question => {
    const mcqText = item.mcq as string
    const correctAnswer = item.mcq_answer as string

    let question = ""
    let options: string[] = []

    // Method 1: Split by A) B) C) D)
    const parts = mcqText.split(/\s*[A-D]\)\s*/)
    if (parts.length >= 2) {
      question = parts[0].trim()
      for (let i = 1; i < parts.length && options.length < 4; i++) {
        const option = parts[i].trim()
        if (option) options.push(option)
      }
    }

    // Method 2: Regex extraction if needed
    if (options.length === 0) {
      const questionMatch = mcqText.match(/^(.*?)(?=\s*[A-D]\))/s)
      if (questionMatch) question = questionMatch[1].trim()

      const optionMatches = mcqText.match(/[A-D]\)\s*([^A-D]*?)(?=\s*[A-D]\)|$)/gs)
      if (optionMatches) {
        options = optionMatches
          .map((m) => m.replace(/^[A-D]\)\s*/, "").trim())
          .filter((o) => o.length > 0)
      }
    }

    if (question) question = question.replace(/^(?:Q\d+:|Question\s+\d+:)\s*/i, "").trim()

    if (!question || options.length === 0) {
      question = mcqText
      options = ["Option A", "Option B", "Option C", "Option D"]
    }

    let correctIndex = -1
    if (correctAnswer) {
      const answerText = correctAnswer.trim()

      const letter = answerText.match(/^([A-D])\b/)
      if (letter) correctIndex = letter[1].charCodeAt(0) - 65

      if (correctIndex === -1) {
        const paren = answerText.match(/^([A-D])\)/)
        if (paren) correctIndex = paren[1].charCodeAt(0) - 65
      }

      if (correctIndex === -1) {
        const answerPrefix = answerText.match(/Answer:\s*([A-D])/i)
        if (answerPrefix) correctIndex = answerPrefix[1].toUpperCase().charCodeAt(0) - 65
      }

      if (correctIndex === -1) {
        const normalized = answerText.toLowerCase().trim()
        for (let i = 0; i < options.length; i++) {
          const opt = options[i].toLowerCase().trim()
          if (opt === normalized || opt.includes(normalized) || normalized.includes(opt)) {
            correctIndex = i
            break
          }
        }
      }
    }

    let questionType = "Text-based"
    if (index < textBasedQuestions) questionType = "Text-based"
    else if (index < textBasedQuestions + inferentialQuestions) questionType = "Inferential"
    else questionType = "Main Idea"

    return {
      id: index + 1,
      type: questionType,
      question,
      options,
      correct: correctIndex,
      explanation:
        "Sample explanation - This will be provided by the API in future updates. The explanation will detail why this answer is correct and provide additional context from the source material.",
      questionType:
        "Sample type - This will categorize the cognitive level (Remember, Understand, Apply, Analyze, Evaluate, Create) in future updates.",
    }
  }

  return (
    <>
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: Text input */}
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
              <UploadPanel
                text={text}
                setText={setText}
                uploadedFile={uploadedFile}
                setUploadedFile={setUploadedFile}
                inputMethod={inputMethod}
                setInputMethod={setInputMethod}
              />
            </CardContent>
          </Card>
        </div>

        {/* Right: Configuration */}
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
              <ConfigPanel
                textBasedQuestions={textBasedQuestions}
                setTextBasedQuestions={setTextBasedQuestions}
                inferentialQuestions={inferentialQuestions}
                setInferentialQuestions={setInferentialQuestions}
                includeMainIdea={includeMainIdea}
                setIncludeMainIdea={setIncludeMainIdea}
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                qualityLevel={qualityLevel}
                setQualityLevel={setQualityLevel}
                totalQuestions={totalQuestions}
                canGenerate={canGenerate}
                isGenerating={isGenerating}
                onGenerate={handleGenerate}
              />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Questions list */}
        <div className="w-full mt-8" data-questions-section>
        {questions.length === 0 ? (
            <div className="border border-border rounded-lg p-8 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-muted rounded-full flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="font-medium text-muted-foreground">No questions yet</h3>
            <p className="text-sm text-muted-foreground mt-1">
                Add your text and click Generate{typeof totalQuestions === "number" ? ` (${totalQuestions} planned)` : ""}.
            </p>
            </div>
        ) : (
            <QuestionsList questions={questions} totalQuestions={totalQuestions} />
        )}
        </div>

      
    </>
  )
}
