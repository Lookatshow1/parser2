"use client";
export const dynamic = "force-dynamic";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  createConnection,
  updateConnection,
  listConnections,
  testConnection,
  syncConnection,
  listConnectionSyncRuns,
  getMetrics,
  ConnectionResponse,
  listOrgs,
  switchOrg,
} from "../../lib/api";
import { getOrgId, getToken, setOrgId } from "../../lib/session";
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

const platforms = ["yandex", "vk", "ozon"];

const platformInfo: Record<string, {
  name: string;
  method: "oauth" | "apikey";
  description: string;
  fields: string[];
}> = {
  yandex: {
    name: "Яндекс Директ",
    method: "oauth",
    description: "Авторизация через OAuth. Нажмите кнопку и войдите в аккаунт Яндекса.",
    fields: [],
  },
  vk: {
    name: "VK Реклама",
    method: "oauth",
    description: "Авторизация через VK ID. Подключите ваш рекламный кабинет VK.",
    fields: [],
  },
  ozon: {
    name: "Ozon Performance",
    method: "apikey",
    description: "Введите API-ключи из личного кабинета Ozon Seller.",
    fields: ["client_id", "client_secret"],
  },
};

const credentialsTemplates: Record<string, string> = {
  yandex: JSON.stringify({ mock: true }),
  ozon: JSON.stringify({ client_id: "", client_secret: "" }),
  vk: JSON.stringify({ access_token: "", version: "5.131", account_id: "" }),
};

const syncStatusVariant: Record<string, "success" | "danger" | "warning" | "muted"> = {
  success: "success",
  failed: "danger",
  running: "warning",
  queued: "warning",
};

const formatStatus = (value?: string | null) => {
  if (!value) return "—";
  return STR.statuses[value as keyof typeof STR.statuses] || value;
};

export default function ConnectionsPage() {
  const router = useRouter();
  const [items, setItems] = useState<ConnectionResponse[]>([]);
  const [orgs, setOrgs] = useState<Array<{ id: number; name: string }>>([]);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(null);
  const [platform, setPlatform] = useState("yandex");
  const [credentialsJson, setCredentialsJson] = useState(credentialsTemplates.yandex);
  const [name, setName] = useState("");
  const [autoSyncEnabled, setAutoSyncEnabled] = useState(false);
  const [autoSyncEveryMinutes, setAutoSyncEveryMinutes] = useState(1440);
  const [autoSyncWindowDays, setAutoSyncWindowDays] = useState(3);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedConnectionId, setSelectedConnectionId] = useState<number | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [syncRuns, setSyncRuns] = useState<Array<{ id: number; status: string; run_type: string; created_at: string; result_json?: Record<string, unknown>; error_text?: string | null }>>([]);
  const [metrics, setMetrics] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [syncingId, setSyncingId] = useState<number | null>(null);

  const defaultDateRange = useMemo(() => {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 13);
    return {
      from: from.toISOString().slice(0, 10),
      to: to.toISOString().slice(0, 10),
    };
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const orgData = await listOrgs();
      setOrgs(orgData.items);
      const data = await listConnections();
      setItems(data.items);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    setDateFrom(defaultDateRange.from);
    setDateTo(defaultDateRange.to);
    setActiveOrgId(getOrgId());
  }, []);

  useEffect(() => {
    if (!selectedConnectionId) return;
    const hasActive = syncRuns.some((run) => run.status === "queued" || run.status === "running");
    if (!hasActive) return;
    const interval = setInterval(() => {
      refreshSyncRuns(selectedConnectionId);
      refreshMetrics(selectedConnectionId);
    }, 2500);
    return () => clearInterval(interval);
  }, [selectedConnectionId, syncRuns]);

  const handleCreate = async () => {
    setError(null);
    setNotice(null);
    try {
      const credentials = JSON.parse(credentialsJson);
      await createConnection({
        platform,
        name: name || null,
        credentials_json: credentials,
        auto_sync_enabled: autoSyncEnabled,
        auto_sync_every_minutes: autoSyncEveryMinutes,
        auto_sync_window_days: autoSyncWindowDays,
      });
      setNotice("Подключение создано");
      toast.success("Подключение создано");
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const toggleAutoSync = async (connectionId: number, enabled: boolean) => {
    setError(null);
    setNotice(null);
    try {
      await updateConnection(connectionId, {
        auto_sync_enabled: enabled,
        auto_sync_every_minutes: autoSyncEveryMinutes,
        auto_sync_window_days: autoSyncWindowDays,
      });
      toast.success("Настройки автосинка обновлены");
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const handleTest = async (connectionId: number) => {
    setError(null);
    setNotice(null);
    try {
      const result = await testConnection(connectionId);
      if (result.ok) {
        const message = result.message ? `Подключение проверено: ${result.message}` : "Подключение работает";
        setNotice(message);
        toast.success(message);
      } else {
        const message = result.message || result.error_code || "Проверка не пройдена";
        setError(message);
        toast.error(message);
      }
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const refreshSyncRuns = async (connectionId: number) => {
    setLoadingRuns(true);
    try {
      const data = await listConnectionSyncRuns(connectionId);
      setSyncRuns(data);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    } finally {
      setLoadingRuns(false);
    }
  };

  const refreshMetrics = async (connectionId: number) => {
    setLoadingMetrics(true);
    try {
      const data = await getMetrics({
        connection_id: connectionId,
        date_from: dateFrom,
        date_to: dateTo,
        group_by: "day",
      });
      setMetrics(data.items);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const handleSync = async (connectionId?: number) => {
    const targetId = connectionId ?? selectedConnectionId;
    if (!targetId) {
      const message = "Выберите подключение для синхронизации";
      setError(message);
      toast.error(message);
      return;
    }
    setError(null);
    setNotice(null);
    setSyncingId(targetId);
    try {
      const run = await syncConnection({
        connection_id: targetId,
        date_from: dateFrom,
        date_to: dateTo,
      });
      setNotice(`Синк поставлен в очередь (run #${run.id})`);
      toast.success("Синхронизация запущена");
      setSelectedConnectionId(targetId);
      await refreshSyncRuns(targetId);
      await refreshMetrics(targetId);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    } finally {
      setSyncingId(null);
    }
  };

  const handleOrgSwitch = async (orgId: string) => {
    setError(null);
    setNotice(null);
    try {
      await switchOrg({ organization_id: Number(orgId) });
      setOrgId(orgId);
      setActiveOrgId(orgId);
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={STR.labels.connections}
        subtitle={STR.pages.connectionsSubtitle}
      />

      <Card>
        <CardContent className="space-y-4">
          {!getToken() && <Badge variant="warning">{STR.messages.loginRequired}</Badge>}
          {getToken() && !getOrgId() && <Badge variant="warning">{STR.messages.selectOrg}</Badge>}
          {error && <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
          {notice && <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">{notice}</div>}
          <div className="grid gap-3 md:grid-cols-[1fr_200px]">
            <div className="space-y-2">
              <Label>{STR.labels.activeOrg}</Label>
              <select
                value={activeOrgId ?? ""}
                onChange={(event) => {
                  const value = event.target.value;
                  if (!value) return;
                  handleOrgSwitch(value);
                }}
                className="h-10 w-full rounded-md border border-border bg-panel-strong px-3 text-sm text-text"
              >
                <option value="">{STR.messages.selectOrg}</option>
                {orgs.map((org) => (
                  <option key={org.id} value={String(org.id)}>
                    #{org.id} {org.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="text-xs text-muted">Активная: {activeOrgId ? `#${activeOrgId}` : "—"}</div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-2">
              <Label>{STR.labels.platform}</Label>
              <select
                value={platform}
                onChange={(event) => {
                  const next = event.target.value;
                  setPlatform(next);
                  if (credentialsTemplates[next]) {
                    setCredentialsJson(credentialsTemplates[next]);
                  }
                }}
                className="h-10 w-full rounded-md border border-border bg-panel-strong px-3 text-sm text-text"
              >
                {platforms.map((item) => (
                  <option key={item} value={item}>
                    {platformInfo[item]?.name || item}
                  </option>
                ))}
              </select>
              {platformInfo[platform] && (
                <p className="text-xs text-muted">{platformInfo[platform].description}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Название</Label>
              <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Мой кабинет" />
            </div>
            {platformInfo[platform]?.method === "oauth" ? (
              <div className="space-y-2">
                <Label>Авторизация</Label>
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={() => {
                    toast.info(`OAuth для ${platformInfo[platform].name} будет добавлен в следующем релизе`);
                  }}
                >
                  Войти через {platform === "yandex" ? "Яндекс" : "VK"}
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                <Label>{STR.labels.credentials}</Label>
                <textarea
                  value={credentialsJson}
                  onChange={(event) => setCredentialsJson(event.target.value)}
                  className="h-20 w-full rounded-md border border-border bg-panel-strong px-3 py-2 text-sm text-text font-mono"
                  placeholder='{"client_id": "...", "client_secret": "..."}'
                />
              </div>
            )}
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <label className="flex items-center gap-2 text-sm text-text">
              <input
                type="checkbox"
                checked={autoSyncEnabled}
                onChange={(event) => setAutoSyncEnabled(event.target.checked)}
              />
              Автосинк включён
            </label>
            <Input
              type="number"
              min={1}
              value={autoSyncEveryMinutes}
              onChange={(event) => setAutoSyncEveryMinutes(Number(event.target.value) || 1)}
              placeholder="Интервал (минуты)"
            />
            <Input
              type="number"
              min={1}
              value={autoSyncWindowDays}
              onChange={(event) => setAutoSyncWindowDays(Number(event.target.value) || 1)}
              placeholder="Окно (дней)"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button onClick={handleCreate}>{STR.actions.create}</Button>
            <Button
              variant="secondary"
              onClick={() => {
                if (!selectedConnectionId) {
                  const message = "Выберите подключение для проверки";
                  setError(message);
                  toast.error(message);
                  return;
                }
                handleTest(selectedConnectionId);
              }}
            >
              {STR.actions.check}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Список подключений</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-20 w-full" />}
          {!loading && items.length === 0 && (
            <EmptyState
              title={STR.messages.noConnections}
              description={STR.pages.connectionsEmptyDesc}
              action={<Button size="sm" onClick={handleCreate}>{STR.actions.create}</Button>}
            />
          )}
          {!loading && items.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>{STR.labels.platform}</TableHead>
                  <TableHead>{STR.labels.status}</TableHead>
                  <TableHead>Последний синк</TableHead>
                  <TableHead>Автосинк</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>#{item.id}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="capitalize">{item.platform}</span>
                        {item.name?.toLowerCase().includes("демо") && <Badge variant="info">Демо</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={syncStatusVariant[item.last_sync_status || ""] || "muted"}>
                        {formatStatus(item.last_sync_status)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted">
                      {item.last_sync_finished_at ?? "—"}
                    </TableCell>
                    <TableCell className="text-muted">
                      {item.auto_sync_enabled ? `Да (${item.auto_sync_every_minutes ?? 0}м / ${item.auto_sync_window_days ?? 0}д)` : "Нет"}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex flex-wrap justify-end gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setSelectedConnectionId(item.id);
                            refreshSyncRuns(item.id);
                            refreshMetrics(item.id);
                          }}
                        >
                          {STR.actions.open}
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleSync(item.id)}
                          disabled={syncingId === item.id || item.last_sync_status === "queued" || item.last_sync_status === "running"}
                        >
                          {item.platform === "yandex" ? STR.actions.runDemo : STR.actions.sync}
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => toggleAutoSync(item.id, !item.auto_sync_enabled)}
                        >
                          {item.auto_sync_enabled ? "Выключить авто" : "Включить авто"}
                        </Button>
                        <Button variant="secondary" size="sm" onClick={() => handleTest(item.id)}>
                          {STR.actions.check}
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => router.push(`/connections/${item.id}`)}>
                          Детали
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{STR.labels.syncRuns}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <Input
              type="number"
              placeholder="ID подключения"
              value={selectedConnectionId ?? ""}
              onChange={(event) => setSelectedConnectionId(Number(event.target.value) || null)}
            />
            <Input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <Input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => handleSync()}>{STR.actions.sync}</Button>
            {selectedConnectionId && (
              <>
                <Button variant="secondary" onClick={() => refreshSyncRuns(selectedConnectionId)}>
                  Обновить синки
                </Button>
                <Button variant="secondary" onClick={() => refreshMetrics(selectedConnectionId)}>
                  Обновить метрики
                </Button>
              </>
            )}
          </div>
          {loadingRuns ? (
            <Skeleton className="h-16 w-full" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Тип</TableHead>
                  <TableHead>{STR.labels.status}</TableHead>
                  <TableHead>Создан</TableHead>
                  <TableHead>Результат</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {syncRuns.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell>#{run.id}</TableCell>
                    <TableCell>{run.run_type}</TableCell>
                    <TableCell>
                      <Badge variant={syncStatusVariant[run.status] || "muted"}>{formatStatus(run.status)}</Badge>
                    </TableCell>
                    <TableCell>{new Date(run.created_at).toLocaleString()}</TableCell>
                    <TableCell className="text-muted">
                      {run.result_json && "inserted" in run.result_json
                        ? `${run.result_json.inserted}/${run.result_json.updated}/${run.result_json.unchanged}`
                        : run.error_text
                          ? String(run.error_text).slice(0, 80)
                          : "—"}
                    </TableCell>
                  </TableRow>
                ))}
                {syncRuns.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted">
                      Синхронизаций пока нет.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{STR.labels.metrics}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {loadingMetrics ? (
            <Skeleton className="h-16 w-full" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Дата</TableHead>
                  <TableHead>Показы</TableHead>
                  <TableHead>Клики</TableHead>
                  <TableHead>Расход</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {metrics.map((row, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{String(row.date || "")}</TableCell>
                    <TableCell>{String(row.impressions || 0)}</TableCell>
                    <TableCell>{String(row.clicks || 0)}</TableCell>
                    <TableCell>{String(row.spend || 0)}</TableCell>
                  </TableRow>
                ))}
                {metrics.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted">
                      {STR.messages.noMetrics}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
