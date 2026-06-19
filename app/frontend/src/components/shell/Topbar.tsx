import { SidebarTrigger } from "@/components/ui/sidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Bell,
  Search,
  ChevronDown,
  Keyboard,
  Building2,
  UserCog,
  LogOut,
  Check,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { SyntheticDataPill } from "@/components/hms/SyntheticDataPill";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuPortal,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link, useNavigate } from "@tanstack/react-router";
import { notifications } from "@/data/notifications";
import { useSession } from "@/lib/session";
import { ROLES, ROLE_LABEL, ROLE_TONE, landingFor, type Role } from "@/lib/rbac";
import { getWorkspace } from "@/data/workspaces";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function Topbar() {
  const unread = notifications.filter((n) => !n.read).length;
  const { session, switchRole, switchWorkspace, signOut } = useSession();
  const navigate = useNavigate();
  const user = session?.user;
  const role = session?.role;

  const onRole = (r: Role) => {
    switchRole(r);
    navigate({ to: landingFor(r) });
  };
  const onSignOut = () => {
    signOut();
    navigate({ to: "/auth/login" });
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur">
      <SidebarTrigger />
      <div className="relative flex-1 max-w-xl">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search patients, docs, chats..." className="h-9 pl-8 pr-16" />
        <kbd className="absolute right-2 top-1/2 -translate-y-1/2 rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
          ⌘K
        </kbd>
      </div>
      <div className="flex items-center gap-3">
        <SyntheticDataPill />
        {session ? (
          <Badge variant="outline" className="hidden gap-1 sm:inline-flex">
            <Building2 className="h-3 w-3" /> {session.workspace.name}
          </Badge>
        ) : null}
        <Button asChild variant="ghost" size="icon" className="relative h-9 w-9">
          <Link to="/notifications">
            <Bell className="h-4 w-4" />
            {unread > 0 ? (
              <span className="absolute right-1 top-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-destructive-foreground">
                {unread}
              </span>
            ) : null}
          </Link>
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 rounded-lg border bg-card px-2 py-1 text-sm hover:bg-accent">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="bg-primary text-xs text-primary-foreground">
                  {user?.initials ?? "?"}
                </AvatarFallback>
              </Avatar>
              <div className="hidden flex-col items-start leading-tight md:flex">
                <span className="text-xs font-semibold">{user?.name ?? "Sign in"}</span>
                <span className={cn("text-[10px]", role && ROLE_TONE[role], "rounded px-1")}>
                  {role ? ROLE_LABEL[role] : "—"}
                </span>
              </div>
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60">
            <DropdownMenuLabel>Signed in as</DropdownMenuLabel>
            <DropdownMenuItem disabled>{user?.email ?? "—"}</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <UserCog className="mr-2 h-3.5 w-3.5" /> Switch role
              </DropdownMenuSubTrigger>
              <DropdownMenuPortal>
                <DropdownMenuSubContent>
                  {ROLES.map((r) => (
                    <DropdownMenuItem key={r.id} onSelect={() => onRole(r.id)}>
                      {role === r.id ? (
                        <Check className="mr-2 h-3.5 w-3.5" />
                      ) : (
                        <span className="mr-2 inline-block w-3.5" />
                      )}
                      {r.label}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuSubContent>
              </DropdownMenuPortal>
            </DropdownMenuSub>
            {user && user.availableWorkspaceIds.length > 1 ? (
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Building2 className="mr-2 h-3.5 w-3.5" /> Switch workspace
                </DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    {user.availableWorkspaceIds.map((wid) => {
                      const ws = getWorkspace(wid);
                      const active = session?.workspace.id === wid;
                      return (
                        <DropdownMenuItem key={wid} onSelect={() => switchWorkspace(wid)}>
                          {active ? (
                            <Check className="mr-2 h-3.5 w-3.5" />
                          ) : (
                            <span className="mr-2 inline-block w-3.5" />
                          )}
                          {ws?.name ?? wid}
                        </DropdownMenuItem>
                      );
                    })}
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
            ) : null}
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/settings/profile">Profile</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/settings/workspaces">
                <Building2 className="mr-2 h-3.5 w-3.5" />
                Switch workspace
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/settings/security">Security</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/audit">My audit trail</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/help/shortcuts">
                <Keyboard className="mr-2 h-3.5 w-3.5" />
                Keyboard shortcuts
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={onSignOut}>
              <LogOut className="mr-2 h-3.5 w-3.5" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
