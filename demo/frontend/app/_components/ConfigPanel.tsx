"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Settings, CheckCircle, Zap, Clock } from "lucide-react";

type Props = {
  textBasedQuestions: number;
  setTextBasedQuestions: (n: number) => void;
  inferentialQuestions: number;
  setInferentialQuestions: (n: number) => void;
  includeMainIdea: boolean;
  setIncludeMainIdea: (b: boolean) => void;
  selectedModel: string;
  setSelectedModel: (v: string) => void;
  qualityLevel: string;
  setQualityLevel: (v: string) => void;

  totalQuestions: number;
  canGenerate: boolean;
  isGenerating: boolean;
  onGenerate: () => void;
};

export default function ConfigPanel(props: Props) {
  const {
    textBasedQuestions,
    setTextBasedQuestions,
    inferentialQuestions,
    setInferentialQuestions,
    includeMainIdea,
    setIncludeMainIdea,
    selectedModel,
    setSelectedModel,
    qualityLevel,
    setQualityLevel,
    totalQuestions,
    canGenerate,
    isGenerating,
    onGenerate,
  } = props;

  return (
    <div className="h-full flex flex-col space-y-4">
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
                onChange={(e) =>
                  setTextBasedQuestions(
                    Math.max(0, Number.parseInt(e.target.value) || 0)
                  )
                }
                className="w-16 h-8 custom-input"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Questions directly answered from the text
            </p>
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
                onChange={(e) =>
                  setInferentialQuestions(
                    Math.max(0, Number.parseInt(e.target.value) || 0)
                  )
                }
                className="w-16 h-8 custom-input"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Questions requiring analysis beyond the text
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="main-idea"
                checked={includeMainIdea}
                onCheckedChange={(checked) => setIncludeMainIdea(!!checked)}
              />
              <Label htmlFor="main-idea" className="text-sm">
                Main Idea Question
              </Label>
            </div>
            <p className="text-xs text-muted-foreground ml-6">
              One question about the central theme
            </p>
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
            <RadioGroup
              value={qualityLevel}
              onValueChange={setQualityLevel}
              className="space-y-1"
            >
              <div
                className="flex items-center space-x-2 p-2 rounded border border-gray-300 hover:bg-muted/50 cursor-pointer"
                onClick={() => setQualityLevel("high")}
              >
                <RadioGroupItem value="high" id="high" />
                <div className="flex-1">
                  <Label
                    htmlFor="high"
                    className="flex items-center gap-2 cursor-pointer text-sm"
                  >
                    <CheckCircle className="h-3 w-3 text-gray-600" />
                    <span>High Quality</span>
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Best accuracy, slower
                  </p>
                </div>
              </div>
              <div
                className="flex items-center space-x-2 p-2 rounded border border-gray-300 hover:bg-muted/50 cursor-pointer"
                onClick={() => setQualityLevel("fast")}
              >
                <RadioGroupItem value="fast" id="fast" />
                <div className="flex-1">
                  <Label
                    htmlFor="fast"
                    className="flex items-center gap-2 cursor-pointer text-sm"
                  >
                    <Zap className="h-3 w-3 text-gray-600" />
                    <span>Fast Generation</span>
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Quick results, good quality
                  </p>
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
              {Math.ceil(
                totalQuestions * (qualityLevel === "high" ? 1 : 0.5)
              )}{" "}
              min
            </span>
          </div>
        </div>
      </div>

      <Button
        onClick={onGenerate}
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
            <Settings className="h-4 w-4 mr-2" />
            Generate {totalQuestions}
          </>
        )}
      </Button>
    </div>
  );
}
