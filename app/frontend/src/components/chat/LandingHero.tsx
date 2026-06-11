"use client";

import { Sparkles } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface LandingHeroProps {
  greeting?: string;
  subtitle?: string;
}

export function LandingHero({ greeting, subtitle }: LandingHeroProps) {
  const { user } = useAuth();

  // Compute time-of-day greeting
  const hour = new Date().getHours();
  const timeGreeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  const displayGreeting = greeting || `${timeGreeting}, ${user?.full_name?.split(" ").slice(-1)[0] || "Doctor"}`;
  const displaySubtitle = subtitle || "How can I assist with patient care today?";

  return (
    <div className="flex flex-col items-center py-12 px-6">
      <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mb-5">
        <Sparkles className="w-8 h-8 text-primary-500" />
      </div>
      <h1 className="text-h2 text-text-strong mb-2">{displayGreeting}</h1>
      <p className="text-body text-text-muted max-w-md text-center">{displaySubtitle}</p>
    </div>
  );
}
