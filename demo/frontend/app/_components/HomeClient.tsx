"use client";

import { useState, useEffect, useRef } from "react";
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
import BlockingOverlay from "./BlockingOverlay";

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
  const [fullText, setFullText] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const { show, hide } = useOverlay();

  // config state
  const [textBasedQuestions, setTextBasedQuestions] = useState(1);
  const [inferentialQuestions, setInferentialQuestions] = useState(1);
  const [includeMainIdea, setIncludeMainIdea] = useState(true);
  const [selectedModel, setSelectedModel] = useState("gpt-4o");
  const [qualityLevel, setQualityLevel] = useState<"fast" | "high">("fast");

  // generation state
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationId, setGenerationId] = useState(0);

  // error state
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // abort controller ref for current generation
  const abortControllerRef = useRef<AbortController | null>(null);
  const abortedByUserRef = useRef(false);

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
    setQuestions([]); // clear immediately so old content disappears
    setGenerationId((id) => id + 1);

    // create new abort controller for this generation
    if (abortControllerRef.current) {
      // if somehow one exists, abort it first to be safe
      try {
        abortControllerRef.current.abort();
      } catch {}
    }
    const ctrl = new AbortController();
    abortControllerRef.current = ctrl;

    show();
    setIsGenerating(true);
    try {
      const requestPayload = {
        text: fullText && fullText.length > 0 ? fullText : text,
        fact: textBasedQuestions,
        inference: inferentialQuestions,
        main_idea: includeMainIdea ? 1 : 0,
        quality_first: qualityLevel === "high" ? "yes" : "no",
      };

      // pass the abort signal to postJSON so it can cancel the fetch
      const apiData = await postJSON<any[]>("/generate_mcq", requestPayload, {
        signal: ctrl.signal,
      });

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

      let msg = "Something went wrong generating questions.";

      if (abortedByUserRef.current) {
        msg = "Generation aborted by user.";
        // reset the flag
        abortedByUserRef.current = false;
      } else if (e instanceof ApiError) {
        if (e.code === "NETWORK")
          msg =
            "Cannot reach the generator. Check your internet connection (or CORS).";
        else if (e.code?.startsWith("HTTP_"))
          msg = `Generator error ${e.status}${
            e.detail ? ` — ${e.detail}` : ""
          }`;
        else if (e.code === "PARSE") msg = "Generator returned invalid JSON.";
        else if (e.code === "TIMEOUT")
          msg = "This took too long and was aborted.";
      } else if (e instanceof Error && e.message) {
        msg = e.message;
      }

      setErrorMsg(msg);
    } finally {
      // cleanup controller ref if it still points to this generation
      if (abortControllerRef.current === ctrl)
        abortControllerRef.current = null;
      abortedByUserRef.current = false;
    }
  };

  // Abort handler called by the overlay button
  const handleAbort = () => {
    // mark as user-abort
    abortedByUserRef.current = true;

    if (abortControllerRef.current) {
      try {
        abortControllerRef.current.abort();
      } catch {}
      abortControllerRef.current = null;
    }
    hide();
    setIsGenerating(false);
    setQuestions([]);
    setErrorMsg("Generation aborted by user.");
  };

  const parseQuestionItem = (item: any, index: number): Question => {
    let mcqText = (item.mcq ?? "").trim();
    //normalize common escape sequences and clean up
    mcqText = mcqText
      .replace(/\\r/g, "") // literal "\r"
      .replace(/\\n/g, "\n") // literal "\n" -> newline
      .replace(/\\t/g, "\t") // literal "\t" -> tab
      .replace(/\u00A0/g, " ") // NBSP -> space
      .replace(/\u200B/g, "") // zero-width space -> remove
      .replace(/\r/g, ""); // remove any stray CRs
    const correctAnswer = (item.mcq_answer ?? "").trim();
    const apiExplanation =
      typeof item.explanation === "string" ? item.explanation : "";
    const apiType = String(item.question_type ?? "").toLowerCase(); // "fact" | "inference" | "main_idea"
    const displayType = TYPE_LABEL[apiType] ?? "Text-based";

    let question = "";
    let options: string[] = [];

    // Only treat A)/B)/C)/D) as option markers when they are standalone tokens.
    // Use \b before letter so "(KD)" won't match because 'D' there is not a word boundary (it's part of 'KD').
    // Step 1: find the first valid option marker (A) ... D) that is a token boundary)
    const firstOptionMatch = mcqText.match(/\b([A-D])\)\s*/);
    if (firstOptionMatch) {
      const markerIndex = mcqText.search(/\b[A-D]\)\s*/);
      if (markerIndex !== -1) {
        // question is everything before that marker
        question = mcqText.slice(0, markerIndex).trim();

        // Now extract options robustly: match A) ... up to next valid marker or end
        const optionRe = /\b([A-D])\)\s*([\s\S]*?)(?=(?:\b[A-D]\)\s*)|$)/g;
        const matches = [];
        let m;
        while ((m = optionRe.exec(mcqText)) !== null) {
          // m[1] is letter, m[2] is option text
          const optText = m[2].trim();
          if (optText.length > 0) {
            // ensure order A-D; avoid duplicates
            matches.push({ letter: m[1], text: optText });
          }
          // break early if we have 4 options
          if (matches.length >= 4) break;
        }

        // sort by letter order and fill options array
        matches.sort((a, b) => a.letter.charCodeAt(0) - b.letter.charCodeAt(0));
        options = matches.map((x) => x.text).slice(0, 4);
      }
    }

    // Fallback: simple split by A)/B)/C)/D) if nothing found yet
    if (options.length === 0) {
      // only split if marker is a token boundary
      const parts = mcqText.split(/\b[A-D]\)\s*/);
      if (parts.length >= 2) {
        question = parts[0].trim();
        for (let i = 1; i < parts.length && options.length < 4; i++) {
          const option = parts[i].trim();
          if (option) options.push(option);
        }
      }
    }

    // Another fallback: try regex extraction similar to original but ensure \b before [A-D]
    if (options.length === 0) {
      const questionMatch = mcqText.match(/^(.*?)(?=\b[A-D]\))/s);
      if (questionMatch) question = questionMatch[1].trim();

      const optionMatches = mcqText.match(
        /\b[A-D]\)\s*([^A-D]*?)(?=(?:\b[A-D]\)|$))/gs
      );
      if (optionMatches) {
        options = optionMatches
          .map((m) => m.replace(/^\s*[A-D]\)\s*/, "").trim())
          .filter((o) => o.length > 0)
          .slice(0, 4);
      }
    }

    // Final fallback: if still nothing, put the whole mcq text as question and placeholder options
    if (!question && options.length === 0) {
      question = mcqText;
      options = ["Option A", "Option B", "Option C", "Option D"];
    } else if (!question) {
      // ensure question has something
      question = mcqText;
    }

    // sanitize question prefix (remove Q1: etc.)
    if (question)
      question = question.replace(/^(?:Q\d+:|Question\s+\d+:)\s*/i, "").trim();

    // --- determine correctIndex robustly (same logic but a bit more defensive)
    let correctIndex = -1;
    if (correctAnswer) {
      const answerText = correctAnswer.trim();

      // try capturing a leading letter (A/B/C/D) anywhere but prefer standalone token
      const letterToken = answerText.match(/\b([A-D])\b/);
      if (letterToken) correctIndex = letterToken[1].charCodeAt(0) - 65;

      // try capturing form like "A)" after a possible prefix (e.g. "Q1: A) ...")
      if (correctIndex === -1) {
        const paren = answerText.match(/\b([A-D])\)\b/);
        if (paren) correctIndex = paren[1].charCodeAt(0) - 65;
      }

      // try "Answer: A" style
      if (correctIndex === -1) {
        const answerPrefix = answerText.match(/Answer:\s*([A-D])/i);
        if (answerPrefix)
          correctIndex = answerPrefix[1].toUpperCase().charCodeAt(0) - 65;
      }

      // final fuzzy match against option strings
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
        apiExplanation || "No explanation was provided by the generator.",
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
                fullText={fullText}
                setFullText={setFullText}
                uploadedFile={uploadedFile}
                setUploadedFile={setUploadedFile}
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
            key={generationId} // force remount on new generation
            questions={questions}
            totalQuestions={totalQuestions}
          />
        )}
      </div>

      <BlockingOverlay
        message="ReQUESTA is generating questions"
        onAbort={handleAbort}
      />
    </>
  );
}
