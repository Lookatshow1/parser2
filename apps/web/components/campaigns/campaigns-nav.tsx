"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const items = [
  { href: "/campaigns", label: "Кампании", match: (path: string) => path.startsWith("/campaigns") },
  { href: "/drafts", label: "Черновики", match: (path: string) => path.startsWith("/drafts") },
  { href: "/templates", label: "Шаблоны", match: (path: string) => path.startsWith("/templates") },
  { href: "/magic", label: "Магия AI", match: (path: string) => path.startsWith("/magic") },
];

export function CampaignsNav({ className }: { className?: string }) {
  const pathname = usePathname();

  return (
    <nav className={cn("flex flex-wrap items-center gap-2 rounded-xl border border-border bg-panel/70 p-2", className)}>
      {items.map((item) => {
        const isActive = item.match(pathname);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
              isActive ? "bg-accent/20 text-text" : "text-muted hover:bg-panel-strong hover:text-text",
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
