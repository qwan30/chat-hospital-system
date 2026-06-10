import { Stethoscope } from "lucide-react";

interface LandingHeroProps {
  greeting?: string;
  subtitle?: string;
}

export function LandingHero({ greeting = "Good morning, Dr. Chen", subtitle = "How can I assist with patient care today?" }: LandingHeroProps) {
  return (
    <div className="flex flex-col items-center py-12 px-6">
      <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mb-5">
        <Stethoscope className="w-8 h-8 text-primary-500" />
      </div>
      <h1 className="text-h2 text-text-strong mb-2">{greeting}</h1>
      <p className="text-body text-text-muted max-w-md text-center">{subtitle}</p>
    </div>
  );
}
