"use client";
export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  CampaignSummary,
  CampaignTree,
  createCampaignAd,
  createCampaignAdGroup,
  getCampaign,
  getCampaignTree,
  listCampaignEvents,
  publishCampaign,
} from "../../../lib/api";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../../components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../../components/ui/table";

const statusVariant: Record<string, "success" | "danger" | "warning" | "muted"> = {
  draft: "muted",
  active: "success",
  paused: "warning",
  archived: "danger",
};

const statusLabel = (value: string) => ({
  draft: "Черновик",
  active: "Активно",
  paused: "Пауза",
  archived: "Архив",
}[value] || value);

const actionLabel = (value: string) => ({
  created: "Создание",
  updated: "Обновление",
  published: "Публикация",
  paused: "Пауза",
  archived: "Архив",
  deleted: "Удаление",
}[value] || value);

export default function CampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = Number(params.id);
  const [tree, setTree] = useState<CampaignTree | null>(null);
  const [summary, setSummary] = useState<CampaignSummary | null>(null);
  const [events, setEvents] = useState<Array<{ id: number; action: string; payload_json: Record<string, unknown>; created_at: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [groupName, setGroupName] = useState("");
  const [adForm, setAdForm] = useState({ ad_group_id: "", name: "", title: "", text: "", url: "", image_url: "", call_to_action: "Перейти" });

  const load = async () => {
    setLoading(true);
    try {
      const [treeData, campaignData, eventData] = await Promise.all([
        getCampaignTree(campaignId),
        getCampaign(campaignId),
        listCampaignEvents(campaignId),
      ]);
      setTree(treeData.campaign);
      setSummary(campaignData);
      setEvents(eventData.map((item) => ({
        id: item.id,
        action: item.action,
        payload_json: item.payload_json,
        created_at: item.created_at,
      })));
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (Number.isNaN(campaignId)) return;
    load();
  }, [campaignId]);

  const handleAddGroup = async () => {
    if (!groupName.trim()) return;
    try {
      await createCampaignAdGroup({
        campaign_id: campaignId,
        name: groupName,
        status: "draft",
        targeting_json: {},
      });
      setGroupName("");
      await load();
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  const handleAddAd = async () => {
    if (!adForm.ad_group_id || !adForm.name.trim()) return;
    try {
      await createCampaignAd({
        ad_group_id: Number(adForm.ad_group_id),
        name: adForm.name,
        status: "draft",
        landing_url: adForm.url || null,
        creative_json: {
          title: adForm.title || null,
          text: adForm.text || null,
          image_url: adForm.image_url || null,
          call_to_action: adForm.call_to_action || "Перейти",
        },
      });
      setAdForm({ ...adForm, name: "", title: "", text: "", url: "", image_url: "" });
      await load();
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  const handleStatusChange = async (action: "publish" | "pause" | "archive") => {
    try {
      await publishCampaign(campaignId, action);
      await load();
      toast.success("Статус кампании обновлён");
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  const boardGroups = useMemo(() => {
    type AdGroupArray = typeof tree extends null ? never : NonNullable<typeof tree>['ad_groups'];
    const statusMap: Record<string, AdGroupArray> = {
      draft: [],
      active: [],
      paused: [],
      archived: [],
    };
    if (!tree) return statusMap;
    tree.ad_groups.forEach((group) => {
      const key = statusMap[group.status] ? group.status : "draft";
      statusMap[key].push(group);
    });
    return statusMap;
  }, [tree]);

  if (!tree && loading) {
    return <div className="text-sm text-muted">Загрузка...</div>;
  }

  if (!tree) {
    return (
      <div className="space-y-4">
        <div className="text-sm text-muted">Кампания не найдена.</div>
        <Button variant="secondary" onClick={() => router.push("/campaigns")}>Вернуться</Button>
      </div>
    );
  }

  const stats = summary || { ad_groups_count: tree.ad_groups.length, ads_count: tree.ad_groups.reduce((acc, g) => acc + g.ads.length, 0) };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-text">{tree.name}</h1>
          <p className="text-sm text-muted">Платформа: {tree.platform}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={statusVariant[tree.status] || "muted"}>{statusLabel(tree.status)}</Badge>
          <Button size="sm" onClick={() => handleStatusChange("publish")}>Опубликовать</Button>
          <Button size="sm" variant="secondary" onClick={() => handleStatusChange("pause")}>Пауза</Button>
          <Button size="sm" variant="outline" onClick={() => handleStatusChange("archive")}>Архив</Button>
        </div>
      </div>

      <Tabs defaultValue="structure">
        <TabsList>
          <TabsTrigger value="structure">Структура</TabsTrigger>
          <TabsTrigger value="summary">Сводка</TabsTrigger>
          <TabsTrigger value="history">История</TabsTrigger>
        </TabsList>

        <TabsContent value="structure">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Группы</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input value={groupName} onChange={(e) => setGroupName(e.target.value)} placeholder="Название группы" />
                  <Button onClick={handleAddGroup}>Добавить</Button>
                </div>
                {tree.ad_groups.length === 0 && (
                  <div className="rounded-md border border-dashed border-border px-4 py-6 text-center text-sm text-muted">
                    Групп пока нет.
                  </div>
                )}
                {tree.ad_groups.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Название</TableHead>
                        <TableHead>Статус</TableHead>
                        <TableHead>Объявлений</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tree.ad_groups.map((group) => (
                        <TableRow key={group.id}>
                          <TableCell className="font-medium text-text">{group.name}</TableCell>
                          <TableCell>{statusLabel(group.status)}</TableCell>
                          <TableCell>{group.ads.length}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Объявления</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3">
                  <div className="space-y-2">
                    <Label>Группа</Label>
                    <select
                      className="w-full rounded-md border border-border bg-panel px-3 py-2 text-sm text-text"
                      value={adForm.ad_group_id}
                      onChange={(e) => setAdForm({ ...adForm, ad_group_id: e.target.value })}
                    >
                      <option value="">Выберите группу</option>
                      {tree.ad_groups.map((group) => (
                        <option key={group.id} value={group.id}>
                          {group.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label>Название объявления</Label>
                    <Input value={adForm.name} onChange={(e) => setAdForm({ ...adForm, name: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Заголовок</Label>
                    <Input value={adForm.title} onChange={(e) => setAdForm({ ...adForm, title: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Ссылка</Label>
                    <Input value={adForm.url} onChange={(e) => setAdForm({ ...adForm, url: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>CTA</Label>
                    <select
                      className="w-full rounded-md border border-border bg-panel px-3 py-2 text-sm text-text"
                      value={adForm.call_to_action}
                      onChange={(e) => setAdForm({ ...adForm, call_to_action: e.target.value })}
                    >
                      <option value="Перейти">Перейти</option>
                      <option value="Узнать больше">Узнать больше</option>
                      <option value="Купить">Купить</option>
                      <option value="Оставить заявку">Оставить заявку</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label>Изображение (URL)</Label>
                    <Input value={adForm.image_url} onChange={(e) => setAdForm({ ...adForm, image_url: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Текст</Label>
                    <Input value={adForm.text} onChange={(e) => setAdForm({ ...adForm, text: e.target.value })} />
                  </div>
                </div>
                <Button onClick={handleAddAd} disabled={!adForm.ad_group_id || !adForm.name.trim()}>
                  Добавить объявление
                </Button>

                <div className="rounded-md border border-border bg-panel/60 p-4">
                  <div className="text-xs uppercase text-muted">Превью</div>
                  <div className="mt-3 space-y-2">
                    <div className="flex h-32 w-full items-center justify-center rounded-md bg-panel-strong/60 text-xs text-muted">
                      {adForm.image_url ? "Изображение" : "Изображение не задано"}
                    </div>
                    <div className="text-sm font-semibold text-text">{adForm.title || "Заголовок"}</div>
                    <div className="text-sm text-muted">{adForm.text || "Текст объявления"}</div>
                    <div className="text-xs text-accent">{adForm.call_to_action}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="summary">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Группы</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-text">{stats.ad_groups_count}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Объявления</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-text">{stats.ads_count}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Статус</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-text">{statusLabel(tree.status)}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Цель</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted">{tree.objective || "—"}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Бюджет на период</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted">{tree.budget_total ? `${tree.budget_total} ₽` : "—"}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Бюджет на день</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted">{tree.budget_daily ? `${tree.budget_daily} ₽` : "—"}</CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>История изменений</CardTitle>
            </CardHeader>
            <CardContent>
              {events.length === 0 && (
                <div className="text-sm text-muted">Событий пока нет.</div>
              )}
              {events.length > 0 && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Действие</TableHead>
                      <TableHead>Дата</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {events.map((event) => (
                      <TableRow key={event.id}>
                        <TableCell>{actionLabel(event.action)}</TableCell>
                        <TableCell>{new Date(event.created_at).toLocaleString("ru-RU")}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
