"use client";
export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { listCampaigns, Campaign } from "../../lib/api";
import { STR } from "../../lib/strings";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { EmptyState } from "../../components/ui/empty-state";
import { PageHeader } from "../../components/ui/page-header";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { BadgePercent, Beaker, Send, Store, Sparkles } from "lucide-react";
import { cn } from "../../lib/utils";
import { CampaignGrid } from "../../components/campaigns/campaign-grid";

const statusVariant: Record<string, "success" | "danger" | "warning" | "muted"> = {
  draft: "muted",
  active: "success",
  paused: "warning",
  archived: "danger",
};

const statusLabel = (value: string) => STR.statuses[value as keyof typeof STR.statuses] || value;

const platformMeta: Record<string, { label: string; Icon: typeof BadgePercent }> = {
  yandex: { label: "Яндекс", Icon: BadgePercent },
  ozon: { label: "Ozon", Icon: Store },
  vk: { label: "VK", Icon: Send },
  stub: { label: "Stub", Icon: Beaker },
};

export default function CampaignsPage() {
  const router = useRouter();
  const [items, setItems] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query.trim()) return items;
    const needle = query.toLowerCase();
    return items.filter((item) => item.name.toLowerCase().includes(needle));
  }, [items, query]);

  const load = async () => {
    setLoading(true);
    try {
      const data = await listCampaigns({
        platform: platform || undefined,
        status: status || undefined,
        search: query || undefined,
      });
      setItems(data.items);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [platform, status, query]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text mb-1">Кампании</h1>
          <p className="text-muted text-sm">Управляйте вашими рекламными активами в одном месте</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => router.push("/magic-launch")}
            className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white font-medium shadow-lg shadow-violet-500/20"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Magic Launch
          </Button>
          <Button variant="outline" onClick={() => router.push("/campaigns/new")}>
            Ручной режим
          </Button>
        </div>
      </div>

      {/* Magic Stats - Optional summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-panel border-border">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center">
              <BadgePercent className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-text">0 ₽</div>
              <div className="text-xs text-muted">Расход сегодня</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Smart Filters (Pills) */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-panel p-2 rounded-xl border border-border">
        <div className="flex gap-2 p-1 overflow-x-auto w-full md:w-auto scrollbar-hide">
          {['all', 'active', 'paused', 'archived', 'draft'].map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s === 'all' ? '' : s)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
                (status === s || (status === '' && s === 'all'))
                  ? "bg-violet-500/20 text-violet-300 shadow-sm border border-violet-500/20"
                  : "text-muted hover:text-text hover:bg-white/5"
              )}
            >
              {s === 'all' ? 'Все' : statusLabel(s)}
            </button>
          ))}
        </div>

        <div className="flex gap-2 w-full md:w-auto">
          <div className="relative w-full md:w-64">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Поиск кампаний..."
              className="pl-9 bg-black/20 border-white/5 focus:border-violet-500/50"
            />
            <Store className="w-4 h-4 text-muted absolute left-3 top-3 opacity-50" />
          </div>
        </div>
      </div>

      {/* Grid Content */}
      <div className="min-h-[400px]">
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-[200px] w-full rounded-xl" />)}
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <EmptyState
            title="Кампаний не найдено"
            description={query ? "Попробуйте изменить параметры поиска" : "Запустите вашу первую кампанию через Magic Launch"}
            action={
              !query ? (
                <Button onClick={() => router.push("/magic-launch")} className="bg-gradient-to-r from-violet-600 to-fuchsia-600">
                  <Sparkles className="w-4 h-4 mr-2" />
                  Запустить рекламу
                </Button>
              ) : undefined
            }
          />
        )}

        {!loading && filtered.length > 0 && (
          <CampaignGrid campaigns={filtered} onUpdate={load} />
        )}
      </div>
    </div>
  );
}
