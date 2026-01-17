"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, BarChart3, ChevronDown, Cog, CreditCard, LayoutDashboard, Megaphone, Sparkles, Users, LogOut, UserCircle2, FileText, Menu, X, TrendingUp } from "lucide-react";


import { getActiveOrg, getMe, listOrgs, switchOrg } from "../lib/api";
import { clearOrgId, clearRefreshToken, clearToken, getOrgId, getToken, setOrgId } from "../lib/session";
import { STR } from "../lib/strings";
import { cn } from "../lib/utils";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "./ui/dropdown-menu";

const navItems = [
  { href: "/dashboard", label: STR.nav.dashboard, icon: LayoutDashboard },
  { href: "/analytics", label: "Аналитика", icon: BarChart3 },
  { href: "/magic", label: "Magic Create", icon: Sparkles },
  { href: "/drafts", label: "Черновики", icon: FileText },
  { href: "/ab-tests", label: "A/B Тесты", icon: Activity },
  { href: "/budget-optimizer", label: "Оптимизатор", icon: TrendingUp },
  { href: "/campaigns", label: STR.nav.campaigns, icon: Megaphone },
  { href: "/connections", label: STR.nav.connections, icon: Cog },
  { href: "/autopilot", label: STR.nav.autopilot, icon: Sparkles },
  { href: "/billing", label: "Биллинг", icon: CreditCard },
  { href: "/settings", label: STR.nav.settings, icon: Cog },
];



export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const token = getToken();
  const [orgs, setOrgs] = useState<Array<{ id: number; name: string }>>([]);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(getOrgId());
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [loadingOrgs, setLoadingOrgs] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const canShowShell = useMemo(() => Boolean(token), [token]);


  useEffect(() => {
    if (!token) {
      setUserEmail(null);
      return;
    }
    const load = async () => {
      setLoadingOrgs(true);
      try {
        const [meData, orgData] = await Promise.all([getMe(), listOrgs()]);
        setUserEmail(meData.email);
        setOrgs(orgData.items);
        const active = await getActiveOrg();
        if (active?.id) {
          setActiveOrgId(String(active.id));
          setOrgId(String(active.id));
        }
      } catch {
        setOrgs([]);
      } finally {
        setLoadingOrgs(false);
      }
    };
    load();
  }, [token]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setIsDemo(window.location.hostname === "localhost");
  }, []);

  const handleOrgSwitch = async (value: string) => {
    try {
      const orgId = Number(value);
      const org = await switchOrg({ organization_id: orgId });
      setActiveOrgId(String(org.id));
      setOrgId(String(org.id));
      router.refresh();
    } catch {
      // errors are handled globally
    }
  };

  const handleLogout = () => {
    clearToken();
    clearRefreshToken();
    clearOrgId();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-bg">
      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileMenuOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-64 bg-panel border-r border-border px-4 py-6 animate-slide-in">
            <div className="flex justify-between items-center mb-8">
              <div className="text-lg font-semibold text-text">{STR.appName}</div>
              <button onClick={() => setMobileMenuOpen(false)} className="p-1 text-muted hover:text-text">
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex flex-col gap-1 text-sm">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-3 py-3 text-muted transition-colors hover:bg-panel-strong hover:text-text",
                    pathname === item.href && "bg-panel-strong text-text"
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              ))}
            </nav>
          </aside>
        </div>
      )}

      <div className="mx-auto flex min-h-screen max-w-7xl">
        {/* Desktop Sidebar */}
        <aside className="hidden w-64 flex-col border-r border-border bg-panel px-4 py-6 lg:flex">
          <div className="mb-8 text-lg font-semibold text-text">{STR.appName}</div>
          <nav className="flex flex-col gap-1 text-sm">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-muted transition-colors hover:bg-panel-strong hover:text-text",
                  pathname === item.href && "bg-panel-strong text-text"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <div className="flex flex-1 flex-col">
          <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border bg-panel px-4 py-4 lg:px-6">
            <div className="flex items-center gap-3">
              {/* Mobile hamburger */}
              <button
                onClick={() => setMobileMenuOpen(true)}
                className="p-2 text-muted hover:text-text lg:hidden"
              >
                <Menu className="h-5 w-5" />
              </button>
              <Link href="/" className="text-lg font-semibold text-text lg:hidden">
                {STR.appName}
              </Link>
              {canShowShell && (

                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase text-muted">{STR.labels.activeOrg}</span>
                  <select
                    className="rounded-md border border-border bg-panel-strong px-3 py-2 text-sm text-text"
                    disabled={loadingOrgs || orgs.length === 0}
                    value={activeOrgId ?? ""}
                    onChange={(event) => handleOrgSwitch(event.target.value)}
                  >
                    {orgs.length === 0 && <option value="">{STR.messages.selectOrg}</option>}
                    {orgs.map((org) => (
                      <option key={org.id} value={org.id}>
                        {org.name}
                      </option>
                    ))}
                  </select>
                  {isDemo ? <Badge variant="info">Демо</Badge> : null}
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              {!token && (
                <Button size="sm" onClick={() => router.push("/login")}>{STR.nav.login}</Button>
              )}
              {token && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="secondary" size="sm">
                      <UserCircle2 className="h-4 w-4" />
                      <span className="max-w-[140px] truncate">{userEmail || ""}</span>
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => router.push("/orgs")}>{STR.nav.orgs}</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout}>
                      <LogOut className="h-4 w-4" />
                      {STR.actions.logout}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </header>
          <main className="flex-1 px-6 py-6">
            {!token && (
              <div className="mb-6 rounded-lg border border-border bg-panel-strong px-4 py-3 text-sm text-muted">
                {STR.messages.loginRequired}
              </div>
            )}
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
