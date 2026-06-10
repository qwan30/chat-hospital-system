"use client";

import { LandingHero } from "@/components/chat/LandingHero";
import { SuggestionCard } from "@/components/chat/SuggestionCard";
import { Composer } from "@/components/chat/Composer";
import { FileSearch, Pill, Activity, ClipboardCheck } from "lucide-react";
import { useRouter } from "next/navigation";

export default function ChatLandingPage() {
  const router = useRouter();

  const handleSubmit = (message: string) => {
    router.push("/chat/new?q=" + encodeURIComponent(message));
  };

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <LandingHero />
      <div className="grid grid-cols-2 gap-3">
        <SuggestionCard icon={FileSearch} title="Summarize recent labs" description="Get an AI summary of latest lab results" onClick={() => handleSubmit("Summarize recent labs")} />
        <SuggestionCard icon={Pill} title="Review medications" description="Check for interactions and contraindications" onClick={() => handleSubmit("Review medications")} />
        <SuggestionCard icon={Activity} title="Analyze vitals trend" description="Assess vital signs over the last 48 hours" onClick={() => handleSubmit("Analyze vitals trend")} />
        <SuggestionCard icon={ClipboardCheck} title="Pre-round summary" description="Generate a concise pre-rounding summary" onClick={() => handleSubmit("Pre-round summary")} />
      </div>
      <Composer onSubmit={handleSubmit} />
    </div>
  );
}
