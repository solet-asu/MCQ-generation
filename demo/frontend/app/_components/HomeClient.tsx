"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FileText, Settings, Sparkles } from "lucide-react";

import UploadPanel from "./UploadPanel";
import ConfigPanel from "./ConfigPanel";
import dynamic from "next/dynamic";
import { useOverlay } from "./overlay-store";
import { postJSON, ApiError } from "@/app/util/api";

const QuestionsList = dynamic(() => import("./QuestionsList"), {
  ssr: false,
  loading: () => (
    <div className="text-sm text-muted-foreground">Loading questions…</div>
  ),
});

const TYPE_LABEL: Record<string, string> = {
  fact: "Text-based",
  inference: "Inferential",
  main_idea: "Main Idea",
};

type Question = {
  id: number;
  type: string;
  question: string;
  options: string[];
  correct: number; // -1 if unknown
  explanation: string;
  questionType?: string;
};

export default function HomeClient() {
  // input state
  const [text, setText] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [inputMethod, setInputMethod] = useState("paste");

  const { show, hide } = useOverlay();

  // config state
  const [textBasedQuestions, setTextBasedQuestions] = useState(5);
  const [inferentialQuestions, setInferentialQuestions] = useState(3);
  const [includeMainIdea, setIncludeMainIdea] = useState(true);
  const [selectedModel, setSelectedModel] = useState("gpt-4");
  const [qualityLevel, setQualityLevel] = useState("balanced");

  // generation state
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // error state
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Smooth-scroll to the questions after generation finishes (success OR error)
  useEffect(() => {
    if (isGenerating) return; // only after we finish
    if (questions.length === 0 && !errorMsg) return;

    const el = document.getElementById("questions-section");
    if (!el) return;

    const scroll = () =>
      el.scrollIntoView({ behavior: "smooth", block: "start" });

    // let layout + the dynamic QuestionsList settle
    const raf1 = requestAnimationFrame(() => requestAnimationFrame(scroll));
    const fallback = setTimeout(scroll, 700);

    return () => {
      cancelAnimationFrame(raf1);
      clearTimeout(fallback);
    };
  }, [isGenerating, questions.length, errorMsg]);

  const totalQuestions =
    textBasedQuestions + inferentialQuestions + (includeMainIdea ? 1 : 0);
  const canGenerate =
    (text.trim().length > 50 || !!uploadedFile) && totalQuestions > 0;

  const handleGenerate = async () => {
    setErrorMsg(null); // clear any old error
    show();
    setIsGenerating(true);
    try {
      const requestPayload = {
        text: text,
        fact: textBasedQuestions,
        inference: inferentialQuestions,
        main_idea: includeMainIdea ? 1 : 0,
        quality_first: qualityLevel === "high" ? "yes" : "no",
      };

      const apiData = await postJSON<any[]>("/generate_mcq", requestPayload);

      let parsedQuestions: Question[] = [];
      if (
        Array.isArray(apiData) &&
        apiData.length > 0 &&
        apiData[0].mcq &&
        apiData[0].mcq_answer
      ) {
        parsedQuestions = apiData.map((item: any, index: number) =>
          parseQuestionItem(item, index)
        );
      } else if (
        Array.isArray(apiData) &&
        apiData.length > 0 &&
        apiData[0].system_prompt
      ) {
        throw new Error("API returned unexpected format");
      } else {
        throw new Error("API returned unknown format");
      }

      setQuestions(parsedQuestions);
      setIsGenerating(false);
      hide();
    } catch (e: any) {
      hide();
      console.error("Error generating questions:", e);
      setIsGenerating(false);

      // Friendly messages
      let msg = "Something went wrong generating questions.";
      if (e instanceof ApiError) {
        if (e.code === "NETWORK")
          msg =
            "Cannot reach the generator. Check your internet connection (or CORS).";
        else if (e.code?.startsWith("HTTP_"))
          msg = `Generator error ${e.status}${
            e.detail ? ` — ${e.detail}` : ""
          }`;
        else if (e.code === "PARSE") msg = "Generator returned invalid JSON.";
        else if (e.code === "TIMEOUT")
          msg = "This took too long and was aborted."; // not used by default
      } else if (e instanceof Error && e.message) {
        msg = e.message;
      }
      setErrorMsg(msg);
    }
  };

  const parseQuestionItem = (item: any, index: number): Question => {
    const mcqText = item.mcq as string;
    const correctAnswer = item.mcq_answer as string;
    const apiExplanation =
      typeof item.explanation === "string" ? item.explanation : "";
    const apiType = String(item.question_type ?? "").toLowerCase(); // "fact" | "inference" | "main_idea"
    const displayType = TYPE_LABEL[apiType] ?? "Text-based";

    let question = "";
    let options: string[] = [];

    // Method 1: Split by A) B) C) D)
    const parts = mcqText.split(/\s*[A-D]\)\s*/);
    if (parts.length >= 2) {
      question = parts[0].trim();
      for (let i = 1; i < parts.length && options.length < 4; i++) {
        const option = parts[i].trim();
        if (option) options.push(option);
      }
    }

    // Method 2: Regex extraction if needed
    if (options.length === 0) {
      const questionMatch = mcqText.match(/^(.*?)(?=\s*[A-D]\))/s);
      if (questionMatch) question = questionMatch[1].trim();

      const optionMatches = mcqText.match(
        /[A-D]\)\s*([^A-D]*?)(?=\s*[A-D]\)|$)/gs
      );
      if (optionMatches) {
        options = optionMatches
          .map((m) => m.replace(/^[A-D]\)\s*/, "").trim())
          .filter((o) => o.length > 0);
      }
    }

    if (question)
      question = question.replace(/^(?:Q\d+:|Question\s+\d+:)\s*/i, "").trim();

    if (!question || options.length === 0) {
      question = mcqText;
      options = ["Option A", "Option B", "Option C", "Option D"];
    }

    let correctIndex = -1;
    if (correctAnswer) {
      const answerText = correctAnswer.trim();

      const letter = answerText.match(/^([A-D])\b/);
      if (letter) correctIndex = letter[1].charCodeAt(0) - 65;

      if (correctIndex === -1) {
        const paren = answerText.match(/^([A-D])\)/);
        if (paren) correctIndex = paren[1].charCodeAt(0) - 65;
      }

      if (correctIndex === -1) {
        const answerPrefix = answerText.match(/Answer:\s*([A-D])/i);
        if (answerPrefix)
          correctIndex = answerPrefix[1].toUpperCase().charCodeAt(0) - 65;
      }

      if (correctIndex === -1) {
        const normalized = answerText.toLowerCase().trim();
        for (let i = 0; i < options.length; i++) {
          const opt = options[i].toLowerCase().trim();
          if (
            opt === normalized ||
            opt.includes(normalized) ||
            normalized.includes(opt)
          ) {
            correctIndex = i;
            break;
          }
        }
      }
    }

    return {
      id: index + 1,
      type: displayType,
      question,
      options,
      correct: correctIndex,
      explanation:
        apiExplanation || "No explanation was provided by the generator.", // gentle fallback
    };
  };

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
                Choose how you want to input your academic text for question
                generation
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
              <CardDescription>
                Customize your question settings
              </CardDescription>
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
      <div
        id="questions-section"
        data-questions-section
        className="w-full mt-8 scroll-mt-24 md:scroll-mt-28"
      >
        {errorMsg && (
          <div className="mb-4 rounded-md border border-red-300 bg-red-50 text-red-800 p-3 text-sm">
            {errorMsg}
          </div>
        )}
        {questions.length === 0 ? (
          <div className="border border-border rounded-lg p-8 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-muted rounded-full flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="font-medium text-muted-foreground">
              No questions yet
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Add your text and click Generate
              {typeof totalQuestions === "number"
                ? ` (${totalQuestions} planned)`
                : ""}
              .
            </p>
          </div>
        ) : (
          <QuestionsList
            questions={questions}
            totalQuestions={totalQuestions}
          />
        )}
      </div>
    </>
  );
}
