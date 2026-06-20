import { SidebarTrigger } from "@/components/ui/sidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Bell,
  Search,
  ChevronDown,
  Keyboard,
  Building2,
  LogOut,
  FileText,
  MessageSquare,
  User as UserIcon,
  Loader2,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { SyntheticDataPill } from "@/components/hms/SyntheticDataPill";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link, useNavigate } from "@tanstack/react-router";
import { useSession } from "@/lib/session";
import { ROLE_LABEL, ROLE_TONE, landingFor, type Role } from "@/lib/rbac";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useCallback, useEffect, useRef, useState } from "react";
import { globalSearch, type GlobalSearchResponse } from "@/lib/api/search";

export function Topbar() {
  const unread = 2;
  const { session, signOut } = useSession();
  const navigate = useNavigate();
  const user = session?.user;
  const role = session?.role;

  const onSignOut = () => {
    signOut();
    navigate({ to: "/auth/login" });
  };

  // ── Search state ────────────────────────────────────────────────────
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GlobalSearchResponse | null>(null);
  const [searching, setSearching] = useState(false);
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const doSearch = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResults(null);
      setOpen(false);
      return;
    }
    setSearching(true);
    try {
      const data = await globalSearch(q);
      setResults(data);
      const hasResults =
        data.patients.length > 0 || data.documents.length > 0 || data.threads.length > 0;
      setOpen(hasResults || q.trim().length >= 2);
    } catch {
      setResults(null);
    } finally {
      setSearching(false);
    }
  }, []);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(val), 300);
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // ⌘K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const totalResults =
    (results?.patients.length ?? 0) +
    (results?.documents.length ?? 0) +
    (results?.threads.length ?? 0);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur">
      <SidebarTrigger />
      <div className="relative flex-1 max-w-xl">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          ref={inputRef}
          placeholder="Search patients, docs, chats..."
          className="h-9 pl-8 pr-16"
          value={query}
          onChange={onInputChange}
          onFocus={() => {
            if (query.trim().length >= 2) setOpen(true);
          }}
        />
        {searching ? (
          <Loader2 className="absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        ) : (
          <kbd className="absolute right-2 top-1/2 -translate-y-1/2 rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
            ⌘K
          </kbd>
        )}

        {/* ── Search results dropdown ─────────────────────────── */}
        {open && (
          <div
            ref={dropdownRef}
            className="absolute left-0 top-full z-50 mt-1 w-full rounded-lg border bg-popover p-1 shadow-lg"
          >
            {totalResults === 0 && !searching && (
              <div className="px-3 py-6 text-center text-sm text-muted-foreground">
                No results for "{query}"
              </div>
            )}

            {results && results.patients.length > 0 && (
              <>
                <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Patients
                </div>
                {results.patients.slice(0, 5).map((p) => (
                  <button
                    key={p.id}
                    className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-accent"
                    onClick={() => {
                      setOpen(false);
                      setQuery("");
                      navigate({ to: "/patients/$patientId", params: { patientId: p.id } });
                    }}
                  >
                    <UserIcon className="h-3.5 w-3.5 text-primary" />
                    <span className="truncate font-medium">{p.full_name}</span>
                    <span className="ml-auto font-mono text-xs text-muted-foreground">{p.mrn}</span>
                  </button>
                ))}
              </>
            )}

            {results && results.documents.length > 0 && (
              <>
                <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Documents
                </div>
                {results.documents.slice(0, 5).map((d) => (
                  <button
                    key={d.id}
                    className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-accent"
                    onClick={() => {
                      setOpen(false);
                      setQuery("");
                      navigate({ to: "/documents/$documentId", params: { documentId: d.id } });
                    }}
                  >
                    <FileText className="h-3.5 w-3.5 text-citation" />
                    <span className="truncate font-medium">{d.title}</span>
                    <span className="ml-auto text-xs text-muted-foreground">{d.document_type}</span>
                  </button>
                ))}
              </>
            )}

            {results && results.threads.length > 0 && (
              <>
                <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Chat Threads
                </div>
                {results.threads.slice(0, 5).map((t) => (
                  <button
                    key={t.id}
                    className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-accent"
                    onClick={() => {
                      setOpen(false);
                      setQuery("");
                      navigate({ to: "/chat", search: { thread: t.id } });
                    }}
                  >
                    <MessageSquare className="h-3.5 w-3.5 text-ai" />
                    <span className="truncate font-medium">{t.title || "Untitled thread"}</span>
                  </button>
                ))}
              </>
            )}
          </div>
        )}
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

            <DropdownMenuItem asChild>
              <Link to="/settings/profile">Profile</Link>
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
