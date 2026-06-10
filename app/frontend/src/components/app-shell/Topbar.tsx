"use client";

import { Search, ChevronDown, Database, FlaskConical, GraduationCap, Lock, LogOut, User, Settings, HelpCircle, RefreshCw, Sun } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth-context";
import { PRODUCT_NAME, CURRENT_ENVIRONMENT } from "@/lib/constants";
import { useState } from "react";

interface TopbarProps {
  onOpenCommandPalette: () => void;
}

const ENVIRONMENTS = [
  { id: "synthetic", label: "Synthetic Data", desc: "Mock patient datasets. Safe for testing.", icon: Database, color: "text-primary-600 bg-primary-50", active: true },
  { id: "sandbox", label: "Sandbox", desc: "Isolated environment for development.", icon: FlaskConical, color: "text-warning-500 bg-warning-100" },
  { id: "training", label: "Training Mode", desc: "De-identified historical charts.", icon: GraduationCap, color: "text-purple-600 bg-purple-100" },
  { id: "production", label: "Production Data", desc: "Live hospital intranet data. Strict ABAC.", icon: Lock, color: "text-danger-600 bg-danger-100" },
];

export function Topbar({ onOpenCommandPalette }: TopbarProps) {
  const { user, logout } = useAuth();
  const initials = user?.full_name
    ? user.full_name.split(" ").map((n) => n[0]).join("").toUpperCase()
    : "??";

  return (
    <header
      className="fixed left-[244px] top-0 right-0 z-20 flex items-center justify-between h-[84px] px-6 bg-bg-page border-b border-border-subtle"
    >
      {/* Logo + Product */}
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-600 text-white font-bold text-sm">H</div>
        <span className="text-text-strong font-semibold text-[14px]">{PRODUCT_NAME}</span>
      </div>

      {/* Search trigger */}
      <button
        onClick={onOpenCommandPalette}
        className="flex items-center gap-3 px-4 py-2 bg-bg-surface-tint border border-border-subtle rounded-lg text-text-muted text-[13px] min-w-[320px] hover:border-border-default transition-colors"
      >
        <Search className="w-4 h-4 text-text-subtle" />
        <span className="flex-1 text-left">Search patients, documents, threads...</span>
        <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-bg-surface border border-border-subtle rounded text-text-subtle">⌘K</kbd>
      </button>

      {/* Right: env pill + user */}
      <div className="flex items-center gap-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 px-3 py-1.5 text-[12px] font-medium text-text-muted bg-bg-surface-tint border border-border-subtle rounded-lg hover:border-border-default transition-colors">
              <span className="w-2 h-2 rounded-full bg-primary-500" />
              {CURRENT_ENVIRONMENT}
              <ChevronDown className="w-3 h-3 ml-1" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-[310px]">
            <DropdownMenuLabel className="text-caption-strong text-text-muted">Environment</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {ENVIRONMENTS.map((env) => {
              const Icon = env.icon;
              return (
                <DropdownMenuItem key={env.id} className="flex items-start gap-3 py-3 cursor-pointer">
                  <span className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${env.color}`}>
                    <Icon className="w-4 h-4" />
                  </span>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-body-strong text-text-default">{env.label}</span>
                    <span className="text-caption text-text-muted">{env.desc}</span>
                  </div>
                  {env.active && (
                    <span className="ml-auto text-[10px] font-medium px-1.5 py-0.5 rounded bg-success-50 text-success-600">Current</span>
                  )}
                </DropdownMenuItem>
              );
            })}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2.5 pl-2.5 pr-1 py-1 rounded-lg hover:bg-bg-surface-tint transition-colors">
              <div className="text-right">
                <div className="text-[13px] font-medium text-text-default leading-tight">{user?.full_name || "User"}</div>
                <div className="text-[11px] text-text-muted leading-tight">{user?.department || ""}</div>
              </div>
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary-100 text-primary-700 text-[11px] font-semibold">{initials}</AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="text-caption-strong text-text-muted">{user?.full_name}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem><User className="w-4 h-4 mr-2" /> My Profile</DropdownMenuItem>
            <DropdownMenuItem><Settings className="w-4 h-4 mr-2" /> Preferences</DropdownMenuItem>
            <DropdownMenuItem><RefreshCw className="w-4 h-4 mr-2" /> Switch Role</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem><HelpCircle className="w-4 h-4 mr-2" /> Help &amp; Support</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-danger-600 focus:text-danger-600" onClick={logout}>
              <LogOut className="w-4 h-4 mr-2" /> Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
