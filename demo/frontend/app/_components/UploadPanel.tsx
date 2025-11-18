"use client";

import { useCallback, useState } from "react";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Upload, FileText, CheckCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { extractTextClient } from "@/app/util/extract";

type Props = {
  text: string;
  setText: (v: string) => void;
  fullText: string;
  setFullText: (v: string) => void;
  uploadedFile: File | null;
  setUploadedFile: (f: File | null) => void;
};

export default function UploadPanel({
  text,
  setText,
  fullText,
  setFullText,
  uploadedFile,
  setUploadedFile,
}: Props) {
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  // Used when user attempts to upload but textarea is non-empty
  const [isUploadConfirmOpen, setIsUploadConfirmOpen] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  const MAX_WORDS = 10000; // word limit for processing and UI display

  // For informing the user we truncated their text
  const [isTruncated, setIsTruncated] = useState(false);
  const [truncatedOriginalWordCount, setTruncatedOriginalWordCount] = useState<
    number | null
  >(null);

  // Helper: truncate to MAX_WORDS (word-aware)
  function truncateToWordLimit(input: string) {
    const words = input.split(/\s+/).filter(Boolean);
    if (words.length <= MAX_WORDS) {
      return { truncated: false, text: input, originalCount: words.length };
    }
    // join with single spaces to keep consistent spacing
    const sliced = words.slice(0, MAX_WORDS).join(" ");
    return { truncated: true, text: sliced, originalCount: words.length };
  }

  const handleFileChosen = useCallback(
    async (file: File | null) => {
      if (!file) return;

      setExtractError(null);
      setIsExtracting(true);
      try {
        const extracted = await extractTextClient(file);

        // truncate by words if needed (this truncated text is canonical)
        const {
          truncated,
          text: truncatedText,
          originalCount,
        } = truncateToWordLimit(extracted);

        // store and display the truncated 10k-word text
        setFullText(truncatedText);
        setText(truncatedText); // show the full truncated 10k words in textarea
        setUploadedFile(file);
        setPendingFile(null);
        setIsUploadConfirmOpen(false);

        setIsTruncated(truncated);
        setTruncatedOriginalWordCount(truncated ? originalCount : null);
      } catch (e: any) {
        console.error("Failed to extract text:", e);
        setExtractError(e?.message || "Could not read file");
      } finally {
        setIsExtracting(false);
      }
    },
    [setText, setUploadedFile, setFullText]
  );

  const handleFileUploadInput = useCallback(
    (ev: React.ChangeEvent<HTMLInputElement>) => {
      const file = ev.target.files?.[0] ?? null;
      if (!file) return;

      // if textarea has content -> ask for confirmation before replacing
      if (text.trim().length > 0) {
        setPendingFile(file);
        setIsUploadConfirmOpen(true);
      } else {
        // no content -> proceed directly
        void handleFileChosen(file);
      }

      // reset input so same file can be re-picked if needed
      ev.currentTarget.value = "";
    },
    [text, handleFileChosen]
  );

  const handleUploadConfirm = async () => {
    if (!pendingFile) {
      setIsUploadConfirmOpen(false);
      return;
    }
    await handleFileChosen(pendingFile);
  };

  const handleUploadCancel = () => {
    setPendingFile(null);
    setIsUploadConfirmOpen(false);
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="text-input">Academic Text Input</Label>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              PDF, DOCX, TXT
            </span>

            <input
              type="file"
              id="file-upload"
              accept=".pdf,.docx,.txt"
              onChange={handleFileUploadInput}
              className="hidden"
            />

            <Button
              variant="outline"
              size="sm"
              onClick={() => document.getElementById("file-upload")?.click()}
              className="bg-white hover:bg-muted text-gray-900 font-medium border border-gray-300 shadow-sm transition-colors"
              title="Upload PDF, DOCX, or TXT file"
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload File
            </Button>
          </div>
        </div>

        <Textarea
          id="text-input"
          placeholder="Paste your academic text here or upload a document using the button above..."
          value={text}
          onChange={(e) => {
            const v = e.target.value;
            // apply the same 10k-word truncation for manual paste/typing
            const {
              truncated,
              text: truncatedText,
              originalCount,
            } = truncateToWordLimit(v);

            setFullText(truncatedText); // canonical processed text
            setText(truncatedText); // UI shows the truncated-to-10k text
            setIsTruncated(truncated);
            setTruncatedOriginalWordCount(truncated ? originalCount : null);
          }}
          className="min-h-[350px] resize-none"
        />
        <p className="text-xs text-gray-600">
          Text longer than 10,000 words will be automatically truncated.
        </p>

        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{text.length} characters</span>
          <span>~{text.split(/\s+/).filter(Boolean).length} words</span>
        </div>

        {/* Prominent warning if truncation occurred */}
        {isTruncated && truncatedOriginalWordCount !== null && (
          <div className="mt-1 rounded-md border border-yellow-300 bg-yellow-50 text-yellow-900 p-3 text-sm">
            <strong>Note:</strong> Your text exceeded the{" "}
            {MAX_WORDS.toLocaleString()}-word limit and has been truncated to
            the first {MAX_WORDS.toLocaleString()} words. The original contained{" "}
            {truncatedOriginalWordCount.toLocaleString()} words. The generator
            will use only the truncated text.
          </div>
        )}
      </div>

      {/* Uploaded file visual */}
      {uploadedFile && (
        <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
          <FileText className="h-4 w-4 text-asu-maroon" />
          <span className="text-sm font-medium flex-1">
            {uploadedFile.name}
          </span>
          <Badge className="bg-[#78BE20] text-white flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            Uploaded
          </Badge>
        </div>
      )}

      <div className="space-y-1">
        {isExtracting && (
          <p className="text-xs text-muted-foreground">Extracting text…</p>
        )}
        {extractError && (
          <p className="text-xs text-red-600">Error: {extractError}</p>
        )}
      </div>

      <Dialog open={isUploadConfirmOpen} onOpenChange={setIsUploadConfirmOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Replace existing content?</DialogTitle>
            <p className="text-sm text-muted-foreground mt-2">
              You have text in the input field. Uploading this file will replace
              your current content with the extracted text from the file.
            </p>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            {pendingFile && (
              <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
                <FileText className="h-4 w-4" />
                <span className="text-sm font-medium">{pendingFile.name}</span>
              </div>
            )}
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={handleUploadCancel}
                className="bg-white hover:bg-muted text-gray-900 border border-gray-300 shadow-sm transition-colors"
              >
                Cancel
              </Button>
              <Button
                variant="outline"
                onClick={handleUploadConfirm}
                className=" bg-asu-gray-2 hover:bg-asu-gray-1 hover:text-asu-white text-asu-white font-medium border border-gray-300 shadow-sm transition-colors"
              >
                Replace Content
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <div className="bg-muted/30 rounded-lg p-4 space-y-2">
        <h4 className="text-sm font-medium text-asu-maroon">
          Tips for Better Questions:
        </h4>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li className="flex items-start gap-2">
            <span className="text-asu-grey">•</span>
            <span>
              Ensure your text is at least 100 words for optimal question
              generation
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-asu-grey">•</span>
            <span>
              Include clear concepts, definitions, and examples in your text
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-asu-grey">•</span>
            <span>
              Academic papers, textbook chapters, and research articles work
              best
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
}
