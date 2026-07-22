import { useRouterState, Link } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  FileText,
  Clock,
  ShieldCheck,
  BarChart3,
  Settings,
  ShieldQuestion,
  Bell,
  KeyRound,
  Quote,
  Activity,
  Network,
  PillBottle,
  UserCog,
  ListChecks,
  ScrollText,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Wordmark, Logo } from "@/components/hms/Logo";
import { useSession } from "@/lib/session";
import { canAccess, ROLE_LABEL } from "@/lib/rbac";

const groups: {
  label: string;
  items: { title: string; url: string; icon: React.ComponentType<{ className?: string }> }[];
}[] = [
  {
    label: "Workspace",
    items: [
      { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
      { title: "Notifications", url: "/notifications", icon: Bell },
      { title: "Screens index", url: "/screens", icon: ListChecks },
    ],
  },
  {
    label: "Clinical",
    items: [
      { title: "Patients", url: "/patients", icon: Users },
      { title: "Chat", url: "/chat", icon: MessageSquare },
      { title: "Timeline", url: "/timeline", icon: Clock },
      { title: "Medication safety", url: "/pharmacy/review-queue", icon: PillBottle },
    ],
  },
  {
    label: "Knowledge",
    items: [
      { title: "Documents", url: "/documents", icon: FileText },
      { title: "Citations", url: "/citations/c-001", icon: Quote },
      {
        title: "Graph RAG",
        url: "/graph/patients/20000000-0000-0000-0000-000000000003",
        icon: Network,
      },
    ],
  },
  {
    label: "Compliance",
    items: [
      { title: "Audit", url: "/audit", icon: ShieldCheck },
      { title: "Access requests", url: "/access-requests", icon: KeyRound },
      { title: "Access policy", url: "/access-policy", icon: ScrollText },
    ],
  },
  {
    label: "Ops",
    items: [
      { title: "Metrics", url: "/metrics", icon: BarChart3 },
      { title: "Integrations", url: "/integrations/hms", icon: Activity },
    ],
  },
  {
    label: "Admin",
    items: [
      { title: "Roles", url: "/admin/roles", icon: UserCog },
      { title: "Settings", url: "/settings/profile", icon: Settings },
    ],
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const path = useRouterState({ select: (s) => s.location.pathname });
  const { session } = useSession();
  const role = session?.role ?? null;
  const isActive = (url: string) => {
    if (url === "/dashboard") return path === url;
    // Use the first 2 segments to match group "root"
    const root = "/" + url.split("/")[1];
    return path === url || path.startsWith(root + "/");
  };

  const visibleGroups = groups
    .map((g) => ({ ...g, items: g.items.filter((i) => canAccess(role, i.url)) }))
    .filter((g) => g.items.length > 0);

  return (
    <Sidebar collapsible="icon" className="border-r">
      <SidebarHeader className="border-b px-3 py-3">
        {collapsed ? <Logo /> : <Wordmark />}
      </SidebarHeader>
      <SidebarContent>
        {visibleGroups.map((g) => (
          <SidebarGroup key={g.label}>
            <SidebarGroupLabel>{g.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {g.items.map((item) => (
                  <SidebarMenuItem key={item.url}>
                    <SidebarMenuButton asChild isActive={isActive(item.url)} tooltip={item.title}>
                      <Link to={item.url as string}>
                        <item.icon />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter className="border-t p-3">
        {!collapsed ? (
          <div className="rounded-lg border bg-muted/40 p-3 text-xs">
            <div className="flex items-center gap-2">
              <ShieldQuestion className="h-4 w-4 text-secondary" />
              <span className="font-medium text-foreground">Permission-aware</span>
            </div>
            <p className="mt-1 text-muted-foreground">
              Acting as{" "}
              <span className="font-medium text-foreground">{role ? ROLE_LABEL[role] : "—"}</span>.
              RBAC/ABAC enforced.
            </p>
            <p className="mt-2 inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 font-medium text-success">
              <span className="h-1.5 w-1.5 rounded-full bg-success" /> Audit ready
            </p>
          </div>
        ) : (
          <div className="flex justify-center">
            <span className="h-2 w-2 rounded-full bg-success" />
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
