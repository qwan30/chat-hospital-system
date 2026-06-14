"use client";

import { Shield, Lock, Search, LineChart, Check } from "lucide-react";
import Image from "next/image";

export function AuthMarketingPane() {
  const features = [
    {
      icon: Shield,
      iconBg: "bg-primary-100",
      iconColor: "text-primary-600",
      title: "Enterprise-Grade Security",
      desc: "SOC 2 compliant with end-to-end encryption and role-based access control.",
    },
    {
      icon: Lock,
      iconBg: "bg-success-100",
      iconColor: "text-success-600",
      title: "Privacy by Design",
      desc: "Built to protect PHI with data minimization, consent controls, and strict access policies.",
    },
    {
      icon: Search,
      iconBg: "bg-purple-100",
      iconColor: "text-purple-600",
      title: "Trusted & Transparent",
      desc: "All actions are traceable with complete audit logs and explainable AI.",
    },
    {
      icon: LineChart,
      iconBg: "bg-warning-100",
      iconColor: "text-warning-500", // using standard lucide colors/Tailwind
      title: "Built for Healthcare",
      desc: "Designed with clinicians in mind to save time, reduce admin burden, and enhance care.",
    },
  ];

  return (
    <div className="relative z-10 flex flex-col justify-center h-full px-12 xl:px-16 bg-primary-50">
      <div className="mb-8">
        {/* Replace BrandLockup with text or logo matching Figma */}
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-primary-600 rounded-xl shadow-sm text-white font-bold text-lg">
            H
          </div>
          <div className="flex flex-col">
            <span className="text-body-strong text-text-strong">AI-Powered Hospital</span>
            <span className="text-caption text-text-muted">Knowledge Assistant</span>
          </div>
        </div>
      </div>

      <h1 className="text-[28px] leading-[36px] font-bold text-text-strong mb-3 whitespace-pre-line">
        {"Smarter insights.\nBetter patient care."}
      </h1>
      
      <p className="text-[14px] leading-relaxed text-text-default mb-8 max-w-[430px]">
        Securely ingest, search, and analyze medical records, guidelines, and knowledge to accelerate clinical decisions and improve outcomes.
      </p>

      <div className="space-y-3 max-w-[482px]">
        {features.map((f, i) => (
          <div key={i} className="flex items-start gap-4 p-4 bg-white rounded-xl border border-border-subtle shadow-sm">
            <div className={`flex items-center justify-center w-9 h-9 rounded-lg ${f.iconBg}`}>
              <f.icon className={`w-4 h-4 ${f.iconColor}`} />
            </div>
            <div>
              <h3 className="text-[13px] font-bold text-text-strong mb-1">{f.title}</h3>
              <p className="text-[11px] leading-[18px] text-text-muted">{f.desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 flex items-center gap-2 text-[11px] font-bold text-text-default">
        <Shield className="w-4 h-4 text-primary-600" />
        Trusted by healthcare organizations to protect data and improve patient outcomes.
      </div>
    </div>
  );
}
