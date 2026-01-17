"use client";

import { useEffect, useState } from "react";
import { DraftsApi, DraftCampaign } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Trash2, FileText, ArrowRight, Rocket, CreditCard, Sparkles } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { STR } from "@/lib/strings";

export default function DraftsPage() {
    const [drafts, setDrafts] = useState<DraftCampaign[]>([]);
    const [loading, setLoading] = useState(true);
    const [showBanner, setShowBanner] = useState(false);

    useEffect(() => {
        loadDrafts();

        // Check if user just came from magic flow
        const pending = localStorage.getItem("pending_creatives");
        if (pending) {
            setShowBanner(true);
        }
    }, []);

    const loadDrafts = async () => {
        setLoading(true);
        try {
            const data = await DraftsApi.list();
            setDrafts(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm(STR.drafts.deleteConfirm)) return;
        try {
            await DraftsApi.delete(id);
            toast.success("Удалено");
            loadDrafts();
        } catch (e) {
            console.error(e);
        }
    };

    const handlePublish = async (id: number) => {
        try {
            await DraftsApi.publish(id);
            toast.success(STR.drafts.publishSuccess);
            loadDrafts();
        } catch (e) {
            toast.error(STR.drafts.publishError);
        }
    };

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
            {/* Success Banner */}
            {showBanner && drafts.length > 0 && (
                <div className="bg-gradient-to-r from-green-600/20 to-emerald-600/20 border border-green-500/30 rounded-2xl p-6 mb-8">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                                <Sparkles className="h-6 w-6 text-green-400" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">Ваши объявления готовы! 🎉</h3>
                                <p className="text-gray-400">Пополните баланс, чтобы запустить рекламу</p>
                            </div>
                        </div>
                        <Link href="/billing">
                            <Button className="bg-green-600 hover:bg-green-500">
                                <CreditCard className="mr-2 h-4 w-4" />
                                Пополнить баланс
                            </Button>
                        </Link>
                    </div>
                </div>
            )}

            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold">{STR.drafts.title}</h1>
                    <p className="text-gray-400 mt-1">{STR.drafts.subtitle}</p>
                </div>
                <Link href="/magic">
                    <Button className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500">
                        <Sparkles className="mr-2 h-4 w-4" />
                        {STR.drafts.newMagicRun}
                    </Button>
                </Link>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-10 h-10 text-violet-400 animate-spin" />
                </div>
            ) : drafts.length === 0 ? (
                <div className="text-center py-20 border border-dashed border-white/10 rounded-xl bg-white/5">
                    <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-400">{STR.drafts.empty}</h3>
                    <p className="text-gray-500 mt-2 mb-6">{STR.drafts.emptyHint}</p>
                    <Link href="/magic">
                        <Button className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500">
                            <Sparkles className="mr-2 h-4 w-4" />
                            {STR.drafts.goToWizard}
                        </Button>
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {drafts.map((draft) => (
                        <Link key={draft.id} href={`/drafts/${draft.id}`}>
                            <Card className="glass-card border-white/5 hover:border-violet-500/30 transition-all h-full group">
                                <CardHeader>
                                    <div className="flex justify-between items-start">
                                        <CardTitle className="text-white truncate pr-2 group-hover:text-violet-300 transition-colors">
                                            {draft.name}
                                        </CardTitle>
                                        <span className="text-xs bg-violet-500/20 text-violet-400 px-2 py-1 rounded-full uppercase tracking-wider font-semibold">
                                            {draft.platform}
                                        </span>
                                    </div>
                                    <CardDescription className="text-gray-400">
                                        {new Date(draft.created_at).toLocaleDateString('ru-RU')}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex justify-between text-sm text-gray-300 mb-2">
                                        <span>{STR.magic.adGroups}</span>
                                        <span className="text-white">{draft.ad_groups?.length || 0}</span>
                                    </div>
                                    <div className="flex justify-between text-sm text-gray-300">
                                        <span>{STR.drafts.status}</span>
                                        <span className={`capitalize ${draft.status === 'published' ? 'text-green-400' : 'text-yellow-400'}`}>
                                            {draft.status === 'published' ? 'Опубликовано' : 'Черновик'}
                                        </span>
                                    </div>
                                </CardContent>
                                <CardFooter className="gap-2">
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="flex-1 text-red-400 hover:text-red-300 hover:bg-red-900/20"
                                        onClick={(e) => { e.preventDefault(); handleDelete(draft.id); }}
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                    <Button
                                        className="flex-[2] bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500"
                                        onClick={(e) => { e.preventDefault(); handlePublish(draft.id); }}
                                        disabled={draft.status === 'published'}
                                    >
                                        {draft.status === 'published' ? (
                                            <>Опубликовано</>
                                        ) : (
                                            <>
                                                <Rocket className="mr-2 w-4 h-4" />
                                                Запустить
                                            </>
                                        )}
                                    </Button>
                                </CardFooter>
                            </Card>
                        </Link>
                    ))}
                </div>
            )}

            {/* Quick Actions */}
            {!loading && drafts.length > 0 && (
                <div className="mt-12 grid md:grid-cols-2 gap-6">
                    <Link href="/billing">
                        <Card className="glass-card border-white/5 hover:border-green-500/30 transition-all cursor-pointer">
                            <CardContent className="p-6 flex items-center gap-4">
                                <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                                    <CreditCard className="h-6 w-6 text-green-400" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-white">Пополнить баланс</h3>
                                    <p className="text-sm text-gray-400">Для запуска рекламы</p>
                                </div>
                                <ArrowRight className="ml-auto h-5 w-5 text-gray-500" />
                            </CardContent>
                        </Card>
                    </Link>
                    <Link href="/analytics">
                        <Card className="glass-card border-white/5 hover:border-violet-500/30 transition-all cursor-pointer">
                            <CardContent className="p-6 flex items-center gap-4">
                                <div className="w-12 h-12 rounded-full bg-violet-500/20 flex items-center justify-center">
                                    <Sparkles className="h-6 w-6 text-violet-400" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-white">Аналитика</h3>
                                    <p className="text-sm text-gray-400">Отслеживайте результаты</p>
                                </div>
                                <ArrowRight className="ml-auto h-5 w-5 text-gray-500" />
                            </CardContent>
                        </Card>
                    </Link>
                </div>
            )}
        </div>
    );
}
