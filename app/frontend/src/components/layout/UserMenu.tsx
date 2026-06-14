"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { User, Settings, HelpCircle, RefreshCw, LogOut } from "lucide-react";
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

export function UserMenu() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : "??";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2.5 pl-2.5 pr-1 py-1 rounded-lg hover:bg-bg-surface-tint transition-colors">
          <div className="text-right">
            <div className="text-[13px] font-medium text-text-default leading-tight">
              {user?.full_name || "User"}
            </div>
            <div className="text-[11px] text-text-muted leading-tight">
              {user?.department || ""}
            </div>
          </div>
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-primary-100 text-primary-700 text-[11px] font-semibold">
              {initials}
            </AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="text-caption-strong text-text-muted">
          {user?.full_name}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => router.push("/settings")}>
          <User className="w-4 h-4 mr-2" /> My Profile
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => router.push("/settings")}>
          <Settings className="w-4 h-4 mr-2" /> Preferences
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() =>
            toast("Role switched", {
              description: "Role switching will be available in a future update.",
            })
          }
        >
          <RefreshCw className="w-4 h-4 mr-2" /> Switch Role
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => window.open("https://help.example.com", "_blank")}
        >
          <HelpCircle className="w-4 h-4 mr-2" /> Help &amp; Support
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-danger-600 focus:text-danger-600"
          onClick={logout}
        >
          <LogOut className="w-4 h-4 mr-2" /> Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
