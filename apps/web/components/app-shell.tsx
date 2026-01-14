"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, BarChart3, ChevronDown, Cog, CreditCard, LayoutDashboard, Megaphone, Sparkles, Users, LogOut, UserCircle2 } from "lucide-react";
import { getActiveOrg, getMe, listOrgs, switchOrg } from "../lib/api";
import { clearOrgId, clearRefreshToken, clearToken, getOrgId, getToken, setOrgId } from "../lib/session";
import { STR } from "../lib/strings";
import { cn } from "../lib/utils";
import { Button } from "./ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "./ui/dropdown-menu";

const navItems = [
  { href: "/dashboard", label: STR.nav.dashboard, icon: LayoutDashboard },
  { href: "/connections", label: STR.nav.connections, icon: Activity },
  { href: "/campaigns", label: STR.nav.campaigns, icon: Megaphone },
  { href: "/metrics", label: STR.nav.metrics, icon: BarChart3 },
  { href: "/recommendations", label: "Рекомендации", icon: Sparkles },
  { href: "/orgs/members", label: STR.nav.members, icon: Users },
  { href: "/orgs/audit", label: STR.nav.audit, icon: Activity },
  { href: "/balance", label: STR.nav.balance, icon: CreditCard },
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
    <div className="min-h-screen bg-slate-950">
      <div className="mx-auto flex min-h-screen max-w-7xl">
        <aside className="hidden w-60 flex-col border-r border-slate-900 bg-slate-950/80 px-4 py-6 lg:flex">
          <div className="mb-8 text-lg font-semibold text-slate-100">{STR.appName}</div>
          <nav className="flex flex-col gap-1 text-sm">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-slate-300 transition-colors hover:bg-slate-900",
                  pathname === item.href && "bg-slate-900 text-white"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <div className="flex flex-1 flex-col">
          <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-900 bg-slate-950/80 px-6 py-4">
            <div className="flex items-center gap-3">
              <Link href="/" className="text-lg font-semibold text-slate-100 lg:hidden">
                {STR.appName}
              </Link>
              {canShowShell && (
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase text-slate-500">{STR.labels.activeOrg}</span>
                  <select
                    className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100"
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
              <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-300">
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
