"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink, Eye, MousePointer, BarChart3 } from "lucide-react";

interface AdPreviewProps {
    title: string;
    text: string;
    landingUrl: string;
    platform?: string;
    utmParams?: {
        source?: string;
        medium?: string;
        campaign?: string;
        content?: string;
    };
}

export function AdPreview({ title, text, landingUrl, platform = "yandex", utmParams }: AdPreviewProps) {
    // Build final URL with UTMs
    const buildFinalUrl = () => {
        if (!utmParams) return landingUrl;

        const url = new URL(landingUrl.startsWith('http') ? landingUrl : `https://${landingUrl}`);
        if (utmParams.source) url.searchParams.set('utm_source', utmParams.source);
        if (utmParams.medium) url.searchParams.set('utm_medium', utmParams.medium);
        if (utmParams.campaign) url.searchParams.set('utm_campaign', utmParams.campaign);
        if (utmParams.content) url.searchParams.set('utm_content', utmParams.content);
        return url.toString();
    };

    const finalUrl = buildFinalUrl();
    const displayDomain = landingUrl.replace(/^https?:\/\//, '').split('/')[0];

    // Mock metrics
    const mockImpressions = Math.floor(Math.random() * 50000) + 10000;
    const mockClicks = Math.floor(mockImpressions * (Math.random() * 0.05 + 0.02));
    const mockCtr = ((mockClicks / mockImpressions) * 100).toFixed(2);

    return (
        <Card className="glass-card border-white/5 overflow-hidden">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500 uppercase tracking-wider">{platform} Preview</span>
                    <span className="text-xs bg-accent/20 text-accent px-2 py-0.5 rounded">Ad</span>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Yandex-style Ad Preview */}
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                    <div className="space-y-2">
                        <h3 className="text-lg font-medium text-accent hover:underline cursor-pointer">
                            {title || "Ad Title"}
                        </h3>
                        <p className="text-sm text-gray-300 leading-relaxed">
                            {text || "Ad description text..."}
                        </p>
                        <div className="flex items-center gap-1 text-xs text-green-400">
                            <ExternalLink className="h-3 w-3" />
                            <span>{displayDomain}</span>
                        </div>
                    </div>
                </div>

                {/* UTM Breakdown */}
                {utmParams && (
                    <div className="bg-black/30 rounded-lg p-3 space-y-2">
                        <h4 className="text-xs text-gray-400 uppercase tracking-wider mb-2">UTM Parameters</h4>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            {utmParams.source && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Source:</span>
                                    <span className="text-white font-mono">{utmParams.source}</span>
                                </div>
                            )}
                            {utmParams.medium && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Medium:</span>
                                    <span className="text-white font-mono">{utmParams.medium}</span>
                                </div>
                            )}
                            {utmParams.campaign && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Campaign:</span>
                                    <span className="text-white font-mono">{utmParams.campaign}</span>
                                </div>
                            )}
                            {utmParams.content && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Content:</span>
                                    <span className="text-white font-mono">{utmParams.content}</span>
                                </div>
                            )}
                        </div>
                        <div className="mt-2 pt-2 border-t border-white/5">
                            <p className="text-xs text-gray-500 break-all font-mono">{finalUrl}</p>
                        </div>
                    </div>
                )}

                {/* Mock Metrics */}
                <div className="grid grid-cols-3 gap-2">
                    <div className="bg-black/20 rounded-lg p-3 text-center">
                        <Eye className="h-4 w-4 mx-auto mb-1 text-gray-400" />
                        <div className="text-lg font-bold text-white">{mockImpressions.toLocaleString()}</div>
                        <div className="text-xs text-gray-500">Est. Impressions</div>
                    </div>
                    <div className="bg-black/20 rounded-lg p-3 text-center">
                        <MousePointer className="h-4 w-4 mx-auto mb-1 text-gray-400" />
                        <div className="text-lg font-bold text-white">{mockClicks.toLocaleString()}</div>
                        <div className="text-xs text-gray-500">Est. Clicks</div>
                    </div>
                    <div className="bg-black/20 rounded-lg p-3 text-center">
                        <BarChart3 className="h-4 w-4 mx-auto mb-1 text-gray-400" />
                        <div className="text-lg font-bold text-accent">{mockCtr}%</div>
                        <div className="text-xs text-gray-500">Est. CTR</div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

export function AdPreviewGrid({ ads }: { ads: AdPreviewProps[] }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ads.map((ad, idx) => (
                <AdPreview key={idx} {...ad} />
            ))}
        </div>
    );
}
