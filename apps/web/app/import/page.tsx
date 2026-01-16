"use client";

import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Download, CheckCircle } from "lucide-react";
import { useRouter } from "next/navigation";

// Mock connections - in real app, fetch from API
const MOCK_CONNECTIONS = [
    { id: 1, name: "Yandex Direct - Main", platform: "yandex" },
    { id: 2, name: "Yandex Direct - Demo", platform: "yandex" },
];

export default function ImportPage() {
    const router = useRouter();
    const [selectedConnection, setSelectedConnection] = useState<string>("");
    const [importing, setImporting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [importedCount, setImportedCount] = useState(0);

    const handleImport = async () => {
        if (!selectedConnection) {
            alert("Please select a connection");
            return;
        }

        setImporting(true);
        setSuccess(false);

        try {
            // Mock API call - in real app, call backend
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Simulate imported drafts
            setImportedCount(2);
            setSuccess(true);
        } catch (e) {
            alert("Import failed");
        } finally {
            setImporting(false);
        }
    };

    const goToDrafts = () => {
        router.push("/drafts");
    };

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
            <h1 className="text-3xl font-bold mb-2">Import Campaigns</h1>
            <p className="text-gray-400 mb-8">Import existing campaigns from your ad platforms as drafts.</p>

            <div className="max-w-xl">
                <Card className="glass-card border-white/5">
                    <CardHeader>
                        <CardTitle>Select Connection</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div>
                            <label className="text-sm text-gray-400 mb-2 block">Ad Platform Connection</label>
                            <Select value={selectedConnection} onValueChange={setSelectedConnection}>
                                <SelectTrigger className="bg-black/30 border-white/10 text-white">
                                    <SelectValue placeholder="Choose a connection..." />
                                </SelectTrigger>
                                <SelectContent>
                                    {MOCK_CONNECTIONS.map(conn => (
                                        <SelectItem key={conn.id} value={String(conn.id)}>
                                            {conn.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {success ? (
                            <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg text-center">
                                <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
                                <p className="text-green-400 font-medium">Import Successful!</p>
                                <p className="text-sm text-gray-400 mt-1">{importedCount} campaigns imported as drafts</p>
                                <Button onClick={goToDrafts} className="mt-4 bg-accent hover:bg-accent/80">
                                    View Drafts
                                </Button>
                            </div>
                        ) : (
                            <Button
                                onClick={handleImport}
                                disabled={importing || !selectedConnection}
                                className="w-full bg-accent hover:bg-accent/80"
                            >
                                {importing ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Importing...
                                    </>
                                ) : (
                                    <>
                                        <Download className="mr-2 h-4 w-4" />
                                        Import Campaigns
                                    </>
                                )}
                            </Button>
                        )}

                        <p className="text-xs text-gray-500">
                            This will fetch all active campaigns from the selected platform and create draft copies for review.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
