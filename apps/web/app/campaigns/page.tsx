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
import { BadgePercent, Beaker, Send, Store } from "lucide-react";
import { CampaignsNav } from "../../components/campaigns/campaigns-nav";

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
      <CampaignsNav />
      <PageHeader
        title="Кампании"
        subtitle="Создавайте кампании, группы и объявления в одном месте."
        actions={<Button onClick={() => router.push("/campaigns/new")}>Создать кампанию</Button>}
      />

      <Card>
        <CardHeader>
          <CardTitle>Фильтры</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label>Платформа</Label>
            <select
              className="w-full rounded-md border border-border bg-panel-strong px-3 py-2 text-sm text-text"
              value={platform}
              onChange={(event) => setPlatform(event.target.value)}
            >
              <option value="">Все</option>
              <option value="yandex">Яндекс</option>
              <option value="ozon">Ozon</option>
              <option value="vk">VK</option>
              <option value="stub">Stub</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label>Статус</Label>
            <select
              className="w-full rounded-md border border-border bg-panel-strong px-3 py-2 text-sm text-text"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              <option value="">Все</option>
              <option value="draft">Черновик</option>
              <option value="active">Активно</option>
              <option value="paused">Пауза</option>
              <option value="archived">Архив</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label>Поиск</Label>
            <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Название кампании" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Список кампаний</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="space-y-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          )}
          {!loading && filtered.length === 0 && (
            <EmptyState
              title="Кампаний пока нет"
              description="Создайте первую кампанию и начните наполнять структуру."
              action={<Button size="sm" onClick={() => router.push("/campaigns/new")}>Создать кампанию</Button>}
            />
          )}
          {!loading && filtered.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Название</TableHead>
                  <TableHead>Платформа</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead>Бюджет</TableHead>
                  <TableHead>Обновлено</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium text-text">{item.name}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-text">
                        {(() => {
                          const Icon = platformMeta[item.platform]?.Icon;
                          return Icon ? <Icon className="h-4 w-4 text-muted" /> : null;
                        })()}
                        <span>{platformMeta[item.platform]?.label || item.platform}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusVariant[item.status] || "muted"}>{statusLabel(item.status)}</Badge>
                    </TableCell>
                    <TableCell>{item.budget_total ? `${item.budget_total} ₽` : item.budget_daily ? `${item.budget_daily} ₽/день` : "—"}</TableCell>
                    <TableCell>{new Date(item.updated_at).toLocaleDateString("ru-RU")}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="secondary" size="sm" onClick={() => router.push(`/campaigns/${item.id}`)}>
                        Открыть
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
