import { Upload, Scan, Grid3X3, Brain, CheckCircle } from "lucide-react";

const PIPELINE_STEPS = [
  { icon: Upload, label: "Upload", description: "File received" },
  { icon: Scan, label: "OCR", description: "Text extraction" },
  { icon: Grid3X3, label: "Chunk", description: "Semantic splitting" },
  { icon: Brain, label: "Embed", description: "Vector indexing" },
  { icon: CheckCircle, label: "Ready", description: "Available for search" },
];

interface OCRPipelineStepperProps {
  currentStep: number;
}

export function OCRPipelineStepper({ currentStep = 0 }: OCRPipelineStepperProps) {
  return (
    <div className="flex items-center gap-0">
      {PIPELINE_STEPS.map((step, i) => (
        <div key={i} className="flex items-center flex-1">
          <div className="flex flex-col items-center gap-1">
            <span className={"w-8 h-8 rounded-full flex items-center justify-center " + (i < currentStep ? "bg-success-50 text-success-600" : i === currentStep ? "bg-primary-50 text-primary-600 ring-2 ring-primary-200" : "bg-bg-surface-tint text-text-subtle")}>
              {i < currentStep ? <CheckCircle className="w-4 h-4" /> : <step.icon className="w-4 h-4" />}
            </span>
            <span className="text-[10px] font-medium text-text-subtle">{step.label}</span>
          </div>
          {i < PIPELINE_STEPS.length - 1 && <div className={"flex-1 h-0.5 mx-1 rounded " + (i < currentStep ? "bg-success-200" : "bg-border-subtle")} />}
        </div>
      ))}
    </div>
  );
}
