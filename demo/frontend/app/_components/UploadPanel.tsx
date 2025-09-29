"use client";

import { useCallback, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Upload, FileText, Type } from "lucide-react";
import { extractTextClient } from "@/app/util/extract";

type Props = {
  text: string;
  setText: (v: string) => void;
  uploadedFile: File | null;
  setUploadedFile: (f: File | null) => void;
  inputMethod: string;
  setInputMethod: (v: string) => void;
};

export default function UploadPanel({
  text,
  setText,
  uploadedFile,
  setUploadedFile,
  inputMethod,
  setInputMethod,
}: Props) {
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);
  const handleFileUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      setExtractError(null);
      setIsExtracting(true);
      try {
        setUploadedFile(file); // reflect in UI
        const extracted = await extractTextClient(file);
        setText(extracted.slice(0, 40000)); // cap to keep textarea snappy
      } catch (e: any) {
        setExtractError(e?.message || "Could not read file");
      } finally {
        setIsExtracting(false);
      }
    },
    [setUploadedFile, setText]
  );

  return (
    <div className="space-y-6 h-full flex flex-col">
      <Tabs
        value={inputMethod}
        onValueChange={setInputMethod}
        className="w-full"
      >
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
                accept=".pdf,.docx,.txt"
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
                    onClick={() =>
                      document.getElementById("file-upload")?.click()
                    }
                    className="mb-2 cursor-pointer"
                  >
                    Choose File
                  </Button>
                  <p className="text-sm text-muted-foreground">
                    PDF, DOCX, TXT files supported
                  </p>
                  {isExtracting && (
                    <p className="text-xs text-muted-foreground">
                      Extracting text…
                    </p>
                  )}
                  {extractError && (
                    <p className="text-xs text-red-600">
                      Error: {extractError}
                    </p>
                  )}
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
        <h4 className="text-sm font-medium text-asu-maroon">
          Tips for Better Questions:
        </h4>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li className="flex items-start gap-2">
            <span className="text-asu-gold">•</span>
            <span>
              Ensure your text is at least 100 words for optimal question
              generation
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-asu-gold">•</span>
            <span>
              Include clear concepts, definitions, and examples in your text
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-asu-gold">•</span>
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
