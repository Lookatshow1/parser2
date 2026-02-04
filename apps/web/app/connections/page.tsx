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
  OAuthApi,
} from "../../lib/api";
import { getOrgId, getToken, setOrgId } from "../../lib/session";
import { STR } from "../../lib/strings";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { PageHeader } from "../../components/ui/page-header";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";

import { ConnectionList } from "../../components/connections/ConnectionList";
import { SyncRunsPanel } from "../../components/connections/SyncRunsPanel";
import { MetricsTable } from "../../components/connections/MetricsTable";

const platforms = ["yandex", "vk", "ozon", "avito"];

const platformInfo: Record<string, {
  name: string;
  method: "oauth" | "apikey" | "oauth-manual";
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
    method: "oauth-manual",
    description: "Авторизация через VK ID. Получите код доступа и введите его ниже.",
    fields: ["code", "account_id"],
  },
  ozon: {
    name: "Ozon Performance",
    method: "apikey",
    description: "Введите API-ключи из личного кабинета Ozon Seller.",
    fields: ["client_id", "client_secret"],
  },
  avito: {
    name: "Авито",
    method: "apikey",
    description: "Введите Client ID и Secret из раздела API на Авито Pro.",
    fields: ["client_id", "client_secret", "user_id"],
  },
};

const credentialsTemplates: Record<string, string> = {
  yandex: JSON.stringify({ mock: true }),
  ozon: JSON.stringify({ client_id: "", client_secret: "" }),
  vk: JSON.stringify({ code: "", account_id: "" }),
  avito: JSON.stringify({ client_id: "", client_secret: "", user_id: "" }),
};

const VK_CLIENT_ID = "Xm3G7VoWTh79zWQP";

interface SyncRun {
  id: number;
  status: string;
  run_type: string;
  created_at: string;
  result_json?: Record<string, unknown>;
  error_text?: string | null;
}

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
  const [syncRuns, setSyncRuns] = useState<SyncRun[]>([]);
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

  const handleSelectConnection = (id: number) => {
    setSelectedConnectionId(id);
    refreshSyncRuns(id);
    refreshMetrics(id);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={STR.labels.connections}
        subtitle={STR.pages.connectionsSubtitle}
      />

      {/* Create Connection Form */}
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
                  onClick={async () => {
                    try {
                      setError(null);
                      toast.loading("Подготовка авторизации...");
                      const { url } = await OAuthApi.getOAuthUrl(platform);
                      // Store state in sessionStorage for callback validation
                      sessionStorage.setItem("oauth_platform", platform);
                      // Redirect to OAuth provider
                      window.location.href = url;
                    } catch (err) {
                      toast.dismiss();
                      const message = (err as Error).message;
                      setError(message);
                      toast.error(message);
                    }
                  }}
                >
                  Войти через {platform === "yandex" ? "Яндекс" : "VK"}
                </Button>
              </div>
            ) : platformInfo[platform]?.method === "oauth-manual" ? (
              <div className="space-y-2">
                <Label>Код доступа VK</Label>
                <div className="flex gap-2 mb-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const url = `https://ads.vk.com/hq/settings/access?action=oauth2&response_type=code&client_id=${VK_CLIENT_ID}&redirect_uri=https://ads.vk.com/hq/settings/access&scope=ads_manager,ads_read`;
                      window.open(url, "_blank");
                    }}
                  >
                    1. Получить код
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={async () => {
                      try {
                        const parsed = JSON.parse(credentialsJson);
                        if (!parsed.code) {
                          toast.error("Введите код авторизации в поле ниже");
                          return;
                        }
                        setError(null);
                        toast.loading("Подключение VK...");
                        const result = await OAuthApi.exchangeCode({
                          platform: "vk",
                          code: parsed.code,
                          account_id: parsed.account_id || undefined,
                        });
                        toast.dismiss();
                        toast.success(result.message);
                        setNotice(`Подключение создано: ${result.message}`);
                        await load();
                      } catch (err) {
                        toast.dismiss();
                        const message = (err as Error).message;
                        setError(message);
                        toast.error(message);
                      }
                    }}
                  >
                    2. Подключить
                  </Button>
                </div>
                <textarea
                  value={credentialsJson}
                  onChange={(event) => setCredentialsJson(event.target.value)}
                  className="h-24 w-full rounded-md border border-border bg-panel-strong px-3 py-2 text-sm text-text font-mono"
                  placeholder='{"code": "вставьте_код_сюда", "account_id": "опционально"}'
                />
                <p className="text-xs text-muted">После нажатия "Получить код" скопируйте код из URL (параметр "code=...") и вставьте выше.</p>
              </div>
            ) : (
              <div className="space-y-2">
                <Label>Ozon Performance API</Label>
                <div className="grid gap-2">
                  <Input
                    placeholder="Client ID"
                    value={(() => { try { return JSON.parse(credentialsJson).client_id || ""; } catch { return ""; } })()}
                    onChange={(event) => {
                      try {
                        const parsed = JSON.parse(credentialsJson);
                        parsed.client_id = event.target.value;
                        setCredentialsJson(JSON.stringify(parsed, null, 2));
                      } catch {
                        setCredentialsJson(JSON.stringify({ client_id: event.target.value, client_secret: "" }));
                      }
                    }}
                  />
                  <Input
                    type="password"
                    placeholder="Client Secret"
                    value={(() => { try { return JSON.parse(credentialsJson).client_secret || ""; } catch { return ""; } })()}
                    onChange={(event) => {
                      try {
                        const parsed = JSON.parse(credentialsJson);
                        parsed.client_secret = event.target.value;
                        setCredentialsJson(JSON.stringify(parsed, null, 2));
                      } catch {
                        setCredentialsJson(JSON.stringify({ client_id: "", client_secret: event.target.value }));
                      }
                    }}
                  />
                  <Button
                    variant="secondary"
                    onClick={async () => {
                      try {
                        const parsed = JSON.parse(credentialsJson);
                        if (!parsed.client_id || !parsed.client_secret) {
                          toast.error("Введите Client ID и Client Secret");
                          return;
                        }
                        setError(null);
                        toast.loading("Подключение Ozon...");
                        const result = await OAuthApi.createOzonConnection(parsed.client_id, parsed.client_secret);
                        toast.dismiss();
                        toast.success(result.message);
                        setNotice(`Подключение создано: ${result.message}`);
                        await load();
                      } catch (err) {
                        toast.dismiss();
                        const message = (err as Error).message;
                        setError(message);
                        toast.error(message);
                      }
                    }}
                  >
                    Подключить Ozon
                  </Button>
                </div>
                <p className="text-xs text-muted">Получите API ключи в <a href="https://seller.ozon.ru/app/settings/api-keys" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">личном кабинете Ozon Seller</a></p>
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

      {/* Connection List */}
      <Card>
        <CardHeader>
          <CardTitle>Список подключений</CardTitle>
        </CardHeader>
        <CardContent>
          <ConnectionList
            items={items}
            loading={loading}
            syncingId={syncingId}
            selectedConnectionId={selectedConnectionId}
            onSelect={handleSelectConnection}
            onSync={handleSync}
            onTest={handleTest}
            onToggleAutoSync={toggleAutoSync}
            onCreate={handleCreate}
          />
        </CardContent>
      </Card>

      {/* Sync Runs Panel */}
      <Card>
        <CardHeader>
          <CardTitle>{STR.labels.syncRuns}</CardTitle>
        </CardHeader>
        <CardContent>
          <SyncRunsPanel
            syncRuns={syncRuns}
            loading={loadingRuns}
            selectedConnectionId={selectedConnectionId}
            dateFrom={dateFrom}
            dateTo={dateTo}
            onConnectionIdChange={setSelectedConnectionId}
            onDateFromChange={setDateFrom}
            onDateToChange={setDateTo}
            onSync={() => handleSync()}
            onRefreshRuns={() => selectedConnectionId && refreshSyncRuns(selectedConnectionId)}
            onRefreshMetrics={() => selectedConnectionId && refreshMetrics(selectedConnectionId)}
          />
        </CardContent>
      </Card>

      {/* Metrics Table */}
      <Card>
        <CardHeader>
          <CardTitle>{STR.labels.metrics}</CardTitle>
        </CardHeader>
        <CardContent>
          <MetricsTable metrics={metrics} loading={loadingMetrics} />
        </CardContent>
      </Card>
    </div>
  );
}
