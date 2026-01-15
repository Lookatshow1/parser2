"use client";

import { useEffect, useState } from "react";
import { STR } from "../../lib/strings";
import { getAutomationSettings, listAutomationActions, listAutomationRuns, runAutomation, updateAutomationSettings } from "../../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Skeleton } from "../../components/ui/skeleton";
import { toast } from "sonner";

type StatusMap = Record<string, string>;

const STATUS_LABELS: StatusMap = {
  running: "В процессе",
  success: "Успешно",
  failed: "Ошибка",
  draft: "Черновик",
  applied: "Применено",
  ignored: "Игнор"
};

export default function AutopilotPage() {
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<Awaited<ReturnType<typeof getAutomationSettings>> | null>(null);
  const [runs, setRuns] = useState<Awaited<ReturnType<typeof listAutomationRuns>>>([]);
  const [actions, setActions] = useState<Awaited<ReturnType<typeof listAutomationActions>>>([]);

  const load = async () => {
    setLoading(true);
    try {
      const [s, r, a] = await Promise.all([
        getAutomationSettings(),
        listAutomationRuns({ limit: 10 }),
        listAutomationActions({ limit: 20 }),
      ]);
      setSettings(s);
      setRuns(r);
      setActions(a);
    } catch (error: any) {
      toast.error(error.message || STR.messages.error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleRun = async () => {
    try {
      await runAutomation();
      toast.success(STR.autopilot.started);
      load();
    } catch (error: any) {
      toast.error(error.message || STR.messages.error);
    }
  };

  const toggleEnabled = async () => {
    if (!settings) return;
    try {
      const updated = await updateAutomationSettings({ is_enabled: !settings.is_enabled });
      setSettings(updated);
      toast.success(updated.is_enabled ? STR.autopilot.resumed : STR.autopilot.paused);
    } catch (error: any) {
      toast.error(error.message || STR.messages.error);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text">{STR.autopilot.title}</h1>
        <p className="text-sm text-muted">{STR.autopilot.subtitle}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{STR.autopilot.stateTitle}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading ? (
              <Skeleton className="h-6 w-36" />
            ) : (
              <div className="flex items-center gap-2 text-sm text-text">
                <Badge variant={settings?.is_enabled ? "success" : "muted"}>
                  {settings?.is_enabled ? STR.autopilot.enabled : STR.autopilot.disabled}
                </Badge>
                <span className="text-muted">
                  {STR.autopilot.interval}: {settings?.run_interval_minutes || 0} мин
                </span>
              </div>
            )}
            <div className="flex gap-2">
              <Button size="sm" onClick={handleRun}>
                {STR.actions.start}
              </Button>
              <Button variant="secondary" size="sm" onClick={toggleEnabled}>
                {settings?.is_enabled ? STR.autopilot.pauseButton : STR.autopilot.enableButton}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">{STR.autopilot.runsTitle}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading ? (
              <Skeleton className="h-24 w-full" />
            ) : runs.length === 0 ? (
              <div className="text-sm text-muted">{STR.autopilot.noRuns}</div>
            ) : (
              <div className="space-y-2 text-sm text-text">
                {runs.map((run) => (
                  <div key={run.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    <div>
                      <div className="font-medium">Запуск #{run.id}</div>
                      <div className="text-xs text-muted">{run.created_at}</div>
                    </div>
                    <Badge variant={run.status === "success" ? "default" : "secondary"}>
                      {STATUS_LABELS[run.status] || run.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{STR.autopilot.actionsTitle}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {loading ? (
            <Skeleton className="h-32 w-full" />
          ) : actions.length === 0 ? (
            <div className="text-sm text-muted">{STR.autopilot.noActions}</div>
          ) : (
            <div className="space-y-2">
              {actions.map((action) => (
                <div key={action.id} className="rounded-md border border-border px-4 py-3">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-text">{action.title}</div>
                    <Badge variant={action.status === "draft" ? "secondary" : "default"}>
                      {STATUS_LABELS[action.status] || action.status}
                    </Badge>
                  </div>
                  <div className="mt-1 text-sm text-muted">{action.description}</div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
