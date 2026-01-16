"use client";

import { useEffect, useState } from "react";
import { DraftsApi, DraftCampaign } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge"; // Assuming this exists or I'll use simple span
import { Loader2, Trash2, Send, FileText, ArrowRight } from "lucide-react";
import Link from "next/link";

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
        if (!confirm("Delete this draft?")) return;
        try {
            await DraftsApi.delete(id);
            loadDrafts();
        } catch (e) {
            alert("Failed to delete");
        }
    };

    const handlePublish = async (id: number) => {
        if (!confirm("Publish this campaign to Yandex?")) return;
        setLoading(true);
        try {
            await DraftsApi.publish(id);
            alert("Campaign published successfully!");
            loadDrafts();
        } catch (e) {
            alert("Failed to publish");
            setLoading(false);
        }
    };

    return (

        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto">
            <div className="flex justify-between items-center mb-10">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Draft Campaigns</h1>
                    <p className="text-gray-400">Manage and publish your AI-generated campaigns.</p>
                </div>
                <Link href="/magic">
                    <Button className="bg-accent hover:bg-accent/90">
                        <span className="mr-2">+</span> New Magic Run
                    </Button>
                </Link>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-10 h-10 text-accent animate-spin" />
                </div>
            ) : drafts.length === 0 ? (
                <div className="text-center py-20 border border-dashed border-white/10 rounded-2xl">
                    <FileText className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-medium text-white mb-2">No drafts yet</h3>
                    <p className="text-gray-500 mb-6">Create your first campaign using our Magic Wizard.</p>
                    <Link href="/magic">
                        <Button variant="outline">Go to Wizard</Button>
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {drafts.map((draft) => (
                        <Card key={draft.id} className="glass-card border-white/5 hover:border-accent/30 transition-colors">
                            <CardHeader>
                                <div className="flex justify-between items-start">
                                    <CardTitle className="text-white truncate pr-2">{draft.name}</CardTitle>
                                    <span className="text-xs bg-accent/20 text-accent px-2 py-1 rounded-full uppercase tracking-wider font-semibold">
                                        {draft.platform}
                                    </span>
                                </div>
                                <CardDescription className="text-gray-400">
                                    {new Date(draft.created_at).toLocaleDateString()}
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="flex justify-between text-sm text-gray-300 mb-2">
                                    <span>Ad Groups</span>
                                    <span className="text-white">{draft.ad_groups?.length || 0}</span>
                                </div>
                                <div className="flex justify-between text-sm text-gray-300">
                                    <span>Status</span>
                                    <span className="capitalize">{draft.status}</span>
                                </div>
                            </CardContent>
                            <CardFooter className="gap-2">
                                <Button variant="ghost" size="sm" className="w-full text-red-400 hover:text-red-300 hover:bg-red-900/20" onClick={() => handleDelete(draft.id)}>
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                                <Button
                                    className="w-full bg-white/5 hover:bg-white/10 text-white border border-white/10"
                                    onClick={() => handlePublish(draft.id)}
                                    disabled={draft.status === 'published'}
                                >
                                    {draft.status === 'published' ? 'Published' : 'Publish to Yandex'} <ArrowRight className="ml-2 w-4 h-4" />
                                </Button>

                            </CardFooter>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
