"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { DraftsApi, DraftCampaign, ConnectionResponse, listConnections } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Save, Send, Loader2, ChevronDown, ChevronRight, Edit2, X, Check } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { STR } from "@/lib/strings";
import { CampaignsNav } from "@/components/campaigns/campaigns-nav";

type EditingAd = { id: number; title: string; text: string } | null;


export default function DraftDetailPage() {
    const params = useParams();
    const draftId = Number(params.id);

    const [draft, setDraft] = useState<DraftCampaign | null>(null);
    const [loading, setLoading] = useState(true);
    const [publishing, setPublishing] = useState(false);
    const [expandedGroups, setExpandedGroups] = useState<Set<number>>(new Set());
    const [editingAd, setEditingAd] = useState<EditingAd>(null);
    const [saving, setSaving] = useState(false);
    const [connections, setConnections] = useState<ConnectionResponse[]>([]);
    const [selectedConnectionId, setSelectedConnectionId] = useState<string>("");
    const [productIdsRaw, setProductIdsRaw] = useState("");
    const [updatingDraft, setUpdatingDraft] = useState(false);

    useEffect(() => {
        loadDraft();
        loadConnections();
    }, [draftId]);

    const loadDraft = async () => {
        setLoading(true);
        try {
            const data = await DraftsApi.get(draftId);
            setDraft(data);
            setSelectedConnectionId(data.connection_id ? String(data.connection_id) : "");
            const ids = data.payload_json?.product_ids;
            setProductIdsRaw(Array.isArray(ids) ? ids.join(", ") : "");
            if (data.ad_groups) {
                setExpandedGroups(new Set(data.ad_groups.map(g => g.id)));
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const loadConnections = async () => {
        try {
            const data = await listConnections();
            setConnections(data.items || []);
        } catch (e) {
            console.error(e);
        }
    };

    const toggleGroup = (groupId: number) => {
        setExpandedGroups(prev => {
            const next = new Set(prev);
            if (next.has(groupId)) next.delete(groupId);
            else next.add(groupId);
            return next;
        });
    };

    const handlePublish = async () => {
        if (!draft) return;
        if (!confirm("Опубликовать эту кампанию на платформе?")) return;
        setPublishing(true);
        try {
            await DraftsApi.publish(draft.id);
            toast.success(STR.drafts.publishSuccess);
            loadDraft();
        } catch (e) {
            toast.error(STR.drafts.publishError);
        } finally {
            setPublishing(false);
        }
    };


    const startEditAd = (ad: { id: number; title?: string; text?: string }) => {
        setEditingAd({ id: ad.id, title: ad.title || "", text: ad.text || "" });
    };

    const cancelEdit = () => setEditingAd(null);

    const saveAd = async () => {
        if (!editingAd) return;
        setSaving(true);
        try {
            await DraftsApi.updateAd(editingAd.id, { title: editingAd.title, text: editingAd.text });
            setEditingAd(null);
            toast.success(STR.drafts.saveSuccess);
            loadDraft();
        } catch (e) {
            toast.error(STR.drafts.saveError);
        } finally {
            setSaving(false);
        }
    };

    const selectedConnection = connections.find((conn) => String(conn.id) === selectedConnectionId) || null;
    const isOzon = selectedConnection?.platform === "ozon";

    const updateDraftConnection = async (value: string) => {
        setSelectedConnectionId(value);
        if (!draft) return;
        if (!value) return;
        setUpdatingDraft(true);
        try {
            await DraftsApi.update(draft.id, { connection_id: Number(value) });
            toast.success("Подключение обновлено");
            loadDraft();
        } catch (e) {
            toast.error("Не удалось обновить подключение");
        } finally {
            setUpdatingDraft(false);
        }
    };

    const saveProductIds = async () => {
        if (!draft) return;
        const productIds = productIdsRaw
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean)
            .map((item) => Number(item))
            .filter((item) => !Number.isNaN(item));
        if (productIds.length === 0) {
            toast.error("Введите корректные ID товаров");
            return;
        }
        setUpdatingDraft(true);
        try {
            await DraftsApi.update(draft.id, { product_ids: productIds });
            toast.success("Товары сохранены");
            loadDraft();
        } catch (e) {
            toast.error("Не удалось сохранить товары");
        } finally {
            setUpdatingDraft(false);
        }
    };


    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-10 h-10 text-accent animate-spin" />
            </div>
        );
    }

    if (!draft) {
        return (
            <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
                <CampaignsNav className="mb-6" />
                <h1 className="text-3xl font-bold mb-4">Черновик не найден</h1>
                <Link href="/drafts">
                    <Button variant="outline"><ArrowLeft className="mr-2 h-4 w-4" /> Назад</Button>
                </Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
            <CampaignsNav className="mb-6" />
            <div className="flex justify-between items-start mb-8">
                <div>
                    <Link href="/drafts" className="text-gray-400 hover:text-white text-sm flex items-center mb-2">
                        <ArrowLeft className="mr-1 h-3 w-3" /> Назад к черновикам
                    </Link>
                    <h1 className="text-3xl font-bold">{draft.name}</h1>
                    <div className="flex items-center gap-3 mt-2">
                        <span className="text-xs bg-accent/20 text-accent px-2 py-1 rounded-full uppercase">{draft.platform}</span>
                        <span className={`text-xs px-2 py-1 rounded-full uppercase ${draft.status === 'published' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                            {draft.status === 'published' ? 'Опубликовано' : draft.status === 'draft' ? 'Черновик' : draft.status}
                        </span>
                    </div>
                </div>
                <Button
                    onClick={handlePublish}
                    disabled={publishing || draft.status === 'published' || !draft.connection_id}
                    className="bg-accent hover:bg-accent/80"
                >
                    {publishing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                    {draft.status === 'published' ? STR.drafts.published : STR.drafts.publish}
                </Button>
            </div>

            <Card className="glass-card border-white/5 mb-6">
                <CardHeader>
                    <CardTitle className="text-white">Подключение для запуска</CardTitle>
                    <CardDescription className="text-gray-400">
                        Выберите рекламный кабинет, чтобы можно было запустить кампанию.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {connections.length === 0 ? (
                        <div className="text-sm text-gray-400">
                            Нет подключений. Перейдите в <Link href="/connections" className="text-accent hover:underline">подключения</Link>.
                        </div>
                    ) : (
                        <div className="space-y-2">
                            <Label>Подключение</Label>
                            <select
                                className="w-full rounded-md border border-border bg-panel px-3 py-2 text-sm text-text"
                                value={selectedConnectionId}
                                onChange={(e) => updateDraftConnection(e.target.value)}
                                disabled={updatingDraft}
                            >
                                <option value="">Выберите подключение</option>
                                {connections.map((conn) => (
                                    <option key={conn.id} value={String(conn.id)}>
                                        {conn.name || conn.platform}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                    {!draft.connection_id && (
                        <div className="text-xs text-amber-300">
                            Без подключения запуск невозможен.
                        </div>
                    )}
                    {isOzon && (
                        <div className="space-y-2">
                            <Label>ID товаров Ozon</Label>
                            <div className="flex flex-wrap gap-2">
                                <Input
                                    value={productIdsRaw}
                                    onChange={(e) => setProductIdsRaw(e.target.value)}
                                    placeholder="12345, 67890"
                                    className="flex-1 bg-black/20 border-white/10 text-white"
                                />
                                <Button onClick={saveProductIds} disabled={updatingDraft} variant="secondary">
                                    Сохранить
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="space-y-4">
                {draft.ad_groups?.length === 0 && (
                    <div className="text-center py-12 border border-dashed border-white/10 rounded-xl">
                        <p className="text-gray-500">Нет групп объявлений в этой кампании.</p>
                    </div>
                )}

                {draft.ad_groups?.map((group) => (
                    <Card key={group.id} className="glass-card border-white/5">
                        <CardHeader className="cursor-pointer" onClick={() => toggleGroup(group.id)}>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    {expandedGroups.has(group.id) ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                                    <CardTitle className="text-white">{group.name}</CardTitle>
                                </div>
                                <span className="text-xs text-gray-500">{group.ads?.length || 0} объявлений</span>
                            </div>
                        </CardHeader>

                        {expandedGroups.has(group.id) && (
                            <CardContent className="space-y-3">
                                {group.ads?.map((ad) => (
                                    <div key={ad.id} className="p-4 bg-black/20 rounded-lg border border-white/5">
                                        {editingAd?.id === ad.id ? (
                                            <div className="space-y-3">
                                                <Input
                                                    value={editingAd.title}
                                                    onChange={(e) => setEditingAd({ ...editingAd, title: e.target.value })}
                                                    placeholder="Заголовок"
                                                    className="bg-black/30 border-white/10 text-white"
                                                />
                                                <Input
                                                    value={editingAd.text}
                                                    onChange={(e) => setEditingAd({ ...editingAd, text: e.target.value })}
                                                    placeholder="Описание"
                                                    className="bg-black/30 border-white/10 text-white"
                                                />
                                                <div className="flex gap-2">
                                                    <Button size="sm" onClick={saveAd} disabled={saving} className="bg-green-600 hover:bg-green-500">
                                                        {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
                                                    </Button>
                                                    <Button size="sm" variant="ghost" onClick={cancelEdit}><X className="h-3 w-3" /></Button>
                                                </div>
                                            </div>
                                        ) : (
                                            <>
                                                <div className="flex justify-between items-start mb-2">
                                                    <h4 className="font-medium text-white">{ad.title || "Без заголовка"}</h4>
                                                    <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white" onClick={() => startEditAd(ad)}>
                                                        <Edit2 className="h-3 w-3" />
                                                    </Button>
                                                </div>
                                                <p className="text-sm text-gray-400 mb-2">{ad.text || "Нет описания"}</p>
                                                {ad.landing_url && (
                                                    <a href={ad.landing_url} target="_blank" rel="noopener noreferrer" className="text-xs text-accent hover:underline">
                                                        {ad.landing_url}
                                                    </a>
                                                )}
                                            </>
                                        )}
                                    </div>
                                ))}
                                {(!group.ads || group.ads.length === 0) && (
                                    <p className="text-sm text-gray-500 text-center py-4">Нет объявлений в этой группе.</p>
                                )}
                            </CardContent>
                        )}
                    </Card>
                ))}
            </div>
        </div>
    );
}
