import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Bookmark, MoreHorizontal, Share2, Printer } from "lucide-react";

interface DetailHeaderProps {
  fullName: string;
  mrn: string;
  dob?: string;
  gender?: string;
  status?: string;
  department?: string;
  attendingPhysician?: string;
}

const STATUS_COLORS: Record<string, string> = {
  active: "bg-success-50 text-success-600 border-success-100",
  admitted: "bg-primary-50 text-primary-600 border-primary-100",
  discharged: "bg-bg-surface-tint text-text-muted border-border-subtle",
  observation: "bg-warning-50 text-warning-500 border-warning-100",
  critical: "bg-danger-50 text-danger-600 border-danger-100",
};

export function DetailHeader({
  fullName,
  mrn,
  dob,
  gender,
  status = "active",
  department,
  attendingPhysician,
}: DetailHeaderProps) {
  const initials = fullName.split(" ").map((n) => n[0]).join("").toUpperCase();
  const statusLabel = status.charAt(0).toUpperCase() + status.slice(1);
  const statusColor = STATUS_COLORS[status] || STATUS_COLORS.active;

  return (
    <div className="flex items-start justify-between">
      <div className="flex items-start gap-4">
        <Avatar className="h-14 w-14 rounded-xl">
          <AvatarFallback className="rounded-xl bg-primary-100 text-primary-700 text-[18px] font-bold">
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-3">
            <h1 className="text-h1 text-text-strong">{fullName}</h1>
            <Badge variant="outline" className={statusColor + " text-[11px] px-2 py-0.5"}>
              {statusLabel}
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-[13px] text-text-muted">
            <span>MRN: {mrn}</span>
            {dob && <span>DOB: {dob}</span>}
            {gender && <span>{gender}</span>}
            {department && <span>{department}</span>}
            {attendingPhysician && <span>Attending: {attendingPhysician}</span>}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="h-8 w-8 text-text-muted hover:text-text-default">
          <Bookmark className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8 text-text-muted hover:text-text-default">
          <Share2 className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8 text-text-muted hover:text-text-default">
          <Printer className="w-4 h-4" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-text-muted hover:text-text-default">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            <DropdownMenuItem>Request Access</DropdownMenuItem>
            <DropdownMenuItem>View Audit Log</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-danger-600">Report Issue</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
