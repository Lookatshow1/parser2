"use client";

import { useEffect, useState } from "react";
import { DraftsApi, DraftCampaign } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Trash2, FileText, ArrowRight } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { STR } from "@/lib/strings";

export default function DraftsPage() {
    const [drafts, setDrafts] = useState<DraftCampaign[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDrafts();
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
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold">{STR.drafts.title}</h1>
                    <p className="text-gray-400 mt-1">{STR.drafts.subtitle}</p>
                </div>
                <Link href="/magic">
                    <Button className="bg-accent hover:bg-accent/80">
                        {STR.drafts.newMagicRun}
                    </Button>
                </Link>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-10 h-10 text-accent animate-spin" />
                </div>
            ) : drafts.length === 0 ? (
                <div className="text-center py-20 border border-dashed border-white/10 rounded-xl">
                    <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-400">{STR.drafts.empty}</h3>
                    <p className="text-gray-500 mt-2 mb-4">{STR.drafts.emptyHint}</p>
                    <Link href="/magic">
                        <Button className="bg-accent hover:bg-accent/80">{STR.drafts.goToWizard}</Button>
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {drafts.map((draft) => (
                        <Link key={draft.id} href={`/drafts/${draft.id}`}>
                            <Card className="glass-card border-white/5 hover:border-accent/30 transition-colors h-full">
                                <CardHeader>
                                    <div className="flex justify-between items-start">
                                        <CardTitle className="text-white truncate pr-2">{draft.name}</CardTitle>
                                        <span className="text-xs bg-accent/20 text-accent px-2 py-1 rounded-full uppercase tracking-wider font-semibold">
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
                                        <span className="capitalize">{draft.status}</span>
                                    </div>
                                </CardContent>
                                <CardFooter className="gap-2">
                                    <Button variant="ghost" size="sm" className="w-full text-red-400 hover:text-red-300 hover:bg-red-900/20" onClick={(e) => { e.preventDefault(); handleDelete(draft.id); }}>
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                    <Button
                                        className="w-full bg-white/5 hover:bg-white/10 text-white border border-white/10"
                                        onClick={(e) => { e.preventDefault(); handlePublish(draft.id); }}
                                        disabled={draft.status === 'published'}
                                    >
                                        {draft.status === 'published' ? STR.drafts.published : STR.drafts.publish} <ArrowRight className="ml-2 w-4 h-4" />
                                    </Button>
                                </CardFooter>
                            </Card>
                        </Link>
                    ))}

                </div>
            )}
        </div>
    );
}
