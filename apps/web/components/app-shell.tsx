"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, useMemo, useCallback } from "react";
import {
  BarChart3, Megaphone, CreditCard,
  ChevronDown, LogOut, UserCircle2, Menu, X,
  LineChart, Target, Gauge, Bell, Plug, Settings,
  Sparkles
} from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "./ui/dropdown-menu";
import { getToken, clearToken, clearRefreshToken, getOrgId, setOrgId, clearOrgId } from "../lib/session";
import { getMe, listOrgs, getActiveOrg, switchOrg } from "../lib/api";
import { STR } from "../lib/strings";

const navItems = [
  { href: "/dashboard", label: "Дашборд", icon: BarChart3 },
  { href: "/campaigns", label: STR.nav.campaigns, icon: Megaphone },
  { href: "/analytics", label: "Аналитика", icon: LineChart },
  { href: "/competitors", label: "Конкуренты", icon: Target },
  { href: "/metrica", label: "Метрика", icon: Gauge },
  { href: "/notifications", label: "Уведомления", icon: Bell },
  { href: "/connections", label: STR.nav.connections, icon: Plug },
  { href: "/billing", label: "Оплата", icon: CreditCard },
  { href: "/settings", label: STR.nav.settings, icon: Settings },
];

/**
 * AppShell - Main layout component
 * 
 * IMPORTANT: All hooks must be unconditional to avoid "more hooks" error
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  // --- ALL HOOKS MUST BE AT THE TOP, UNCONDITIONAL ---
  const [mounted, setMounted] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [orgs, setOrgs] = useState<Array<{ id: number; name: string }>>([]);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [loadingOrgs, setLoadingOrgs] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Public pages that bypass shell
  const publicPages = ["/", "/login", "/signup", "/adminskaya-panel/login"];
  const isPublicPage = useMemo(
    () => publicPages.includes(pathname) || pathname.startsWith("/adminskaya-panel"),
    [pathname]
  );

  // Effect 1: Mount detection + client-side state
  useEffect(() => {
    setMounted(true);
    // These only work client-side
    const t = getToken();
    setToken(t);
    setActiveOrgId(getOrgId());
    setIsDemo(window.location.hostname === "localhost");
  }, []);

  useEffect(() => {
    if (!mounted) {
      return;
    }
    setToken(getToken());
    setActiveOrgId(getOrgId());
  }, [mounted, pathname]);

  useEffect(() => {
    if (!mounted) {
      return;
    }
    const handleStorage = (event: StorageEvent) => {
      if (event.key === "ads_access_token" || event.key === "ads_active_org") {
        setToken(getToken());
        setActiveOrgId(getOrgId());
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [mounted]);

  // Effect 2: Load user data when token is available
  useEffect(() => {
    if (!mounted || !token) {
      return;
    }

    let cancelled = false;

    const loadUserData = async () => {
      setLoadingOrgs(true);
      try {
        const [meData, orgData] = await Promise.all([getMe(), listOrgs()]);
        if (cancelled) return;

        setUserEmail(meData.email);
        setOrgs(orgData.items || []);

        let active = null;
        try {
          active = await getActiveOrg();
        } catch {
          active = null;
        }
        if (!active && orgData.items && orgData.items.length > 0) {
          try {
            active = await switchOrg({ organization_id: orgData.items[0].id });
          } catch {
            active = null;
          }
        }
        if (!cancelled && active?.id) {
          setActiveOrgId(String(active.id));
          setOrgId(String(active.id));
        }
      } catch (e) {
        if (!cancelled) {
          setOrgs([]);
        }
      } finally {
        if (!cancelled) {
          setLoadingOrgs(false);
        }
      }
    };

    loadUserData();

    return () => {
      cancelled = true;
    };
  }, [mounted, token]);

  // Handlers (stable references)
  const handleOrgSwitch = useCallback(async (value: string) => {
    try {
      const orgId = Number(value);
      const org = await switchOrg({ organization_id: orgId });
      setActiveOrgId(String(org.id));
      setOrgId(String(org.id));
      router.refresh();
    } catch {
      // handled by global error
    }
  }, [router]);

  const handleLogout = useCallback(() => {
    clearToken();
    clearRefreshToken();
    clearOrgId();
    router.push("/login");
  }, [router]);

  // --- CONDITIONAL RETURNS ONLY AFTER ALL HOOKS ---

  // 1. Public pages - no shell
  if (isPublicPage) {
    return <>{children}</>;
  }

  // 2. Not mounted yet - minimal loading (prevents hydration mismatch)
  if (!mounted) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-gray-500 text-sm">Загрузка...</div>
      </div>
    );
  }

  // 3. Authenticated shell
  return (
    <div className="min-h-screen bg-bg">
      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="absolute left-0 top-0 h-full w-64 bg-panel border-r border-border px-4 py-6">
            <div className="flex justify-between items-center mb-8">
              <div className="text-lg font-semibold text-text">{STR.appName}</div>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-1 text-muted hover:text-text"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive
                      ? "bg-accent text-text"
                      : "text-muted hover:bg-panel-strong hover:text-text"
                      }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </aside>
        </div>
      )}

      {/* Desktop Sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col border-r border-border bg-panel px-4 py-6">
        <Link href="/" className="flex items-center gap-3 mb-10">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl font-bold text-text">{STR.appName}</span>
        </Link>
        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive
                  ? "bg-accent text-text"
                  : "text-muted hover:bg-panel-strong hover:text-text"
                  }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-border bg-panel px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-2 text-muted hover:text-text lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </button>
            <Link href="/" className="text-lg font-semibold text-text lg:hidden">
              {STR.appName}
            </Link>
            {token && (
              <div className="hidden sm:flex items-center gap-2">
                <span className="text-xs uppercase text-muted">{STR.labels.activeOrg}</span>
                <select
                  className="rounded-md border border-border bg-panel-strong px-3 py-2 text-sm text-text"
                  disabled={loadingOrgs || orgs.length === 0}
                  value={activeOrgId ?? ""}
                  onChange={(e) => handleOrgSwitch(e.target.value)}
                >
                  {orgs.length === 0 && <option value="">{STR.messages.selectOrg}</option>}
                  {orgs.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
                {isDemo && <Badge variant="info">Демо</Badge>}
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            {!token && (
              <Button size="sm" onClick={() => router.push("/login")}>
                {STR.nav.login}
              </Button>
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
                  <DropdownMenuItem onClick={() => router.push("/orgs")}>
                    {STR.nav.orgs}
                  </DropdownMenuItem>
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
  );
}
