"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import {
  listBuilderCampaigns,
  createBuilderCampaign,
  updateBuilderCampaign,
  deleteBuilderCampaign,
  listBuilderAdGroups,
  createBuilderAdGroup,
  updateBuilderAdGroup,
  deleteBuilderAdGroup,
  listBuilderAds,
  createBuilderAd,
  updateBuilderAd,
  deleteBuilderAd,
  getBuilderTree,
  BuilderTreeCampaign,
  BuilderTreeAdGroup,
  BuilderTreeAd
} from "../../../../lib/api";
import { STR } from "../../../../lib/strings";
import { Button } from "../../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";
import { Input } from "../../../../components/ui/input";
import { Label } from "../../../../components/ui/label";
import { Skeleton } from "../../../../components/ui/skeleton";
import { ChevronRight, ChevronDown, Plus, Trash2, Copy, ExternalLink } from "lucide-react";

type Selection = {
  type: "campaign" | "group" | "ad";
  id: number;
  parentId?: number; // for group (campaignId) or ad (groupId)
};

export default function BuilderPage() {
  const params = useParams();
  const experimentId = Number(params?.id);
  const [tree, setTree] = useState<BuilderTreeCampaign[]>([]);
  const [loading, setLoading] = useState(false);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Form states
  const [formData, setFormData] = useState<any>({});
  const [saving, setSaving] = useState(false);

  const loadTree = async () => {
    setLoading(true);
    try {
      const data = await getBuilderTree(experimentId);
      setTree(data.campaigns);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (experimentId) loadTree();
  }, [experimentId]);

  const toggleExpand = (key: string) => {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSelect = (type: "campaign" | "group" | "ad", id: number, parentId?: number) => {
    setSelection({ type, id, parentId });
    // Find data to populate form
    let data = null;
    if (type === "campaign") {
      data = tree.find(c => c.id === id);
    } else if (type === "group") {
      for (const c of tree) {
        const g = c.ad_groups.find(g => g.id === id);
        if (g) { data = g; break; }
      }
    } else if (type === "ad") {
      for (const c of tree) {
        for (const g of c.ad_groups) {
          const a = g.ads.find(a => a.id === id);
          if (a) { data = a; break; }
        }
      }
    }
    if (data) {
      setFormData({ ...data });
    }
  };

  const handleCreateCampaign = async () => {
    const name = prompt("Название кампании:");
    if (!name) return;
    try {
      await createBuilderCampaign(experimentId, { name, platform: "yandex", status: "draft" });
      toast.success("Кампания создана");
      loadTree();
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  const handleCreateGroup = async (campaignId: number) => {
    const name = prompt("Название группы:");
    if (!name) return;
    try {
      await createBuilderAdGroup(campaignId, { name, status: "draft" });
      toast.success("Группа создана");
      loadTree();
      // Auto expand campaign
      setExpanded(prev => ({ ...prev, [`c-${campaignId}`]: true }));
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  const handleCreateAd = async (groupId: number) => {
    const name = prompt("Название объявления:");
    if (!name) return;
    try {
      await createBuilderAd(groupId, { name, status: "draft" });
      toast.success("Объявление создано");
      loadTree();
      // Auto expand group (need to find campaign id for key if needed, but simple reload works)
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  const handleSave = async () => {
    if (!selection) return;
    setSaving(true);
    try {
      if (selection.type === "campaign") {
        await updateBuilderCampaign(selection.id, { name: formData.name, status: formData.status });
      } else if (selection.type === "group") {
        await updateBuilderAdGroup(selection.id, { name: formData.name, status: formData.status });
      } else if (selection.type === "ad") {
        await updateBuilderAd(selection.id, {
          name: formData.name,
          title: formData.title,
          text: formData.text,
          base_url: formData.base_url,
          utm_json: formData.utm_json,
          status: formData.status
        });
      }
      toast.success("Сохранено");
      loadTree();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selection || !confirm("Удалить?")) return;
    try {
      if (selection.type === "campaign") await deleteBuilderCampaign(selection.id);
      if (selection.type === "group") await deleteBuilderAdGroup(selection.id);
      if (selection.type === "ad") await deleteBuilderAd(selection.id);
      toast.success("Удалено");
      setSelection(null);
      loadTree();
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  const updateUtm = (key: string, value: string) => {
    setFormData((prev: any) => ({
      ...prev,
      utm_json: { ...prev.utm_json, [key]: value }
    }));
  };

  const copyLink = () => {
    if (formData.final_url) {
      navigator.clipboard.writeText(formData.final_url);
      toast.success("Ссылка скопирована");
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[350px_1fr] h-[calc(100vh-100px)]">
      {/* Sidebar Tree */}
      <Card className="flex flex-col overflow-hidden">
        <CardHeader className="py-4 px-4 border-b border-border bg-panel/50">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Структура</CardTitle>
            <Button size="sm" variant="secondary" onClick={handleCreateCampaign}><Plus className="h-4 w-4" /></Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-2 space-y-1">
          {loading && !tree.length && <Skeleton className="h-10 w-full" />}
          {tree.map(campaign => (
            <div key={campaign.id} className="space-y-1">
              <div
                className={`flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-panel-strong ${selection?.type === 'campaign' && selection.id === campaign.id ? 'bg-panel-strong ring-1 ring-border' : ''}`}
                onClick={() => handleSelect("campaign", campaign.id)}
              >
                <div
                  className="rounded p-1 hover:bg-panel-strong"
                  onClick={(e) => { e.stopPropagation(); toggleExpand(`c-${campaign.id}`); }}
                >
                  {expanded[`c-${campaign.id}`] ? <ChevronDown className="h-3 w-3 text-muted" /> : <ChevronRight className="h-3 w-3 text-muted" />}
                </div>
                <span className="text-sm font-medium truncate flex-1">{campaign.name}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0"
                  onClick={(e) => { e.stopPropagation(); handleCreateGroup(campaign.id); }}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>

              {expanded[`c-${campaign.id}`] && (
                <div className="ml-3 space-y-1 border-l border-border pl-4">
                  {campaign.ad_groups.map(group => (
                    <div key={group.id} className="space-y-1">
                      <div
                        className={`flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-panel-strong ${selection?.type === 'group' && selection.id === group.id ? 'bg-panel-strong ring-1 ring-border' : ''}`}
                        onClick={() => handleSelect("group", group.id, campaign.id)}
                      >
                        <div
                          className="rounded p-1 hover:bg-panel-strong"
                          onClick={(e) => { e.stopPropagation(); toggleExpand(`g-${group.id}`); }}
                        >
                          {expanded[`g-${group.id}`] ? <ChevronDown className="h-3 w-3 text-muted" /> : <ChevronRight className="h-3 w-3 text-muted" />}
                        </div>
                        <span className="text-sm truncate flex-1">{group.name}</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0"
                          onClick={(e) => { e.stopPropagation(); handleCreateAd(group.id); }}
                        >
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>

                      {expanded[`g-${group.id}`] && (
                        <div className="ml-3 space-y-1 border-l border-border pl-4">
                          {group.ads.map(ad => (
                            <div
                              key={ad.id}
                              className={`flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-panel-strong ${selection?.type === 'ad' && selection.id === ad.id ? 'bg-panel-strong ring-1 ring-border' : ''}`}
                              onClick={() => handleSelect("ad", ad.id, group.id)}
                            >
                              <span className="text-xs text-muted">AD</span>
                              <span className="text-sm truncate flex-1">{ad.name}</span>
                            </div>
                          ))}
                          {!group.ads.length && <div className="text-xs text-muted pl-2 py-1">Нет объявлений</div>}
                        </div>
                      )}
                    </div>
                  ))}
                  {!campaign.ad_groups.length && <div className="text-xs text-muted pl-2 py-1">Нет групп</div>}
                </div>
              )}
            </div>
          ))}
          {!tree.length && !loading && <div className="text-sm text-muted text-center py-4">Нет кампаний</div>}
        </CardContent>
      </Card>

      {/* Editor Panel */}
      <Card className="flex flex-col overflow-hidden">
        <CardHeader className="py-4 px-6 border-b border-border bg-panel/50">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {selection ? (
                selection.type === "campaign" ? "Редактирование кампании" :
                selection.type === "group" ? "Редактирование группы" : "Редактирование объявления"
              ) : "Выберите элемент"}
            </CardTitle>
            {selection && (
              <Button variant="destructive" size="sm" onClick={handleDelete}>
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-6">
          {!selection && (
            <div className="flex h-full items-center justify-center text-muted">
              Выберите элемент слева для редактирования
            </div>
          )}

          {selection && (
            <div className="space-y-6 max-w-2xl">
              <div className="space-y-2">
                <Label>Название</Label>
                <Input
                  value={formData.name || ""}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label>Статус</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-border bg-panel px-3 py-2 text-sm text-text placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:cursor-not-allowed disabled:opacity-50"
                  value={formData.status || "draft"}
                  onChange={e => setFormData({...formData, status: e.target.value})}
                >
                  <option value="draft">Черновик</option>
                  <option value="active">Активно</option>
                  <option value="paused">Пауза</option>
                </select>
              </div>

              {selection.type === "ad" && (
                <>
                  <div className="space-y-2">
                    <Label>Заголовок</Label>
                    <Input
                      value={formData.title || ""}
                      onChange={e => setFormData({...formData, title: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Текст</Label>
                    <textarea
                      className="flex min-h-[80px] w-full rounded-md border border-border bg-panel px-3 py-2 text-sm text-text placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:cursor-not-allowed disabled:opacity-50"
                      value={formData.text || ""}
                      onChange={e => setFormData({...formData, text: e.target.value})}
                    />
                  </div>

                  <div className="pt-4 border-t border-border space-y-4">
                    <h3 className="font-medium text-text">Ссылка и UTM</h3>
                    <div className="space-y-2">
                      <Label>Посадочная страница (Base URL)</Label>
                      <Input
                        placeholder="https://example.com/page"
                        value={formData.base_url || ""}
                        onChange={e => setFormData({...formData, base_url: e.target.value})}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-xs text-muted">utm_source</Label>
                        <Input
                          value={formData.utm_json?.utm_source || ""}
                          onChange={e => updateUtm("utm_source", e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs text-muted">utm_medium</Label>
                        <Input
                          value={formData.utm_json?.utm_medium || ""}
                          onChange={e => updateUtm("utm_medium", e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs text-muted">utm_campaign</Label>
                        <Input
                          value={formData.utm_json?.utm_campaign || ""}
                          onChange={e => updateUtm("utm_campaign", e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs text-muted">utm_content</Label>
                        <Input
                          value={formData.utm_json?.utm_content || ""}
                          onChange={e => updateUtm("utm_content", e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs text-muted">utm_term</Label>
                        <Input
                          value={formData.utm_json?.utm_term || ""}
                          onChange={e => updateUtm("utm_term", e.target.value)}
                        />
                      </div>
                    </div>

                    <div className="rounded-md bg-panel p-3 space-y-2">
                      <Label className="text-xs text-muted">Итоговая ссылка (после сохранения)</Label>
                      <div className="flex gap-2">
                        <div className="flex-1 rounded border border-border bg-panel-strong p-2 text-sm font-mono text-muted break-all">
                          {formData.final_url || "—"}
                        </div>
                        <Button size="icon" variant="secondary" onClick={copyLink} disabled={!formData.final_url}>
                          <Copy className="h-4 w-4" />
                        </Button>
                        {formData.final_url && (
                          <Button size="icon" variant="secondary" onClick={() => window.open(formData.final_url, '_blank')}>
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}

              <div className="pt-4">
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? "Сохранение..." : "Сохранить изменения"}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
