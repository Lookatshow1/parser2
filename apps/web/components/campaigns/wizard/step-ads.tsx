"use client";

import { useState } from "react";
import { Plus, Trash, Upload, Image as ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface StepAdsProps {
    data: any;
    onChange: (data: any) => void;
    onUpload: (file: File) => Promise<{ url: string }>;
}

export function StepAds({ data, onChange, onUpload }: StepAdsProps) {
    const [uploading, setUploading] = useState<number | null>(null);

    const addAd = () => {
        const newId = Math.max(...data.ads.map((a: any) => a.id), 0) + 1;
        onChange({
            ads: [
                ...data.ads,
                { id: newId, name: `Объявление ${newId}`, title: "", text: "", link: "", image_url: "" }
            ]
        });
    };

    const removeAd = (id: number) => {
        onChange({ ads: data.ads.filter((a: any) => a.id !== id) });
    };

    const updateAd = (id: number, field: string, value: any) => {
        onChange({
            ads: data.ads.map((a: any) => a.id === id ? { ...a, [field]: value } : a)
        });
    };

    const handleFileChange = async (id: number, e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(id);
        try {
            const res = await onUpload(file);
            updateAd(id, 'image_url', res.url);
        } catch (err) {
            alert("Ошибка загрузки");
        } finally {
            setUploading(null);
        }
    };

    return (
        <div className="space-y-8">
            {data.ads.map((ad: any, index: number) => (
                <div key={ad.id} className="border border-border rounded-xl p-4 bg-panel-strong/50 relative group">
                    <div className="absolute top-4 right-4">
                        {data.ads.length > 1 && (
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => removeAd(ad.id)}
                                className="text-muted hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                                <Trash className="w-4 h-4" />
                            </Button>
                        )}
                    </div>

                    <h3 className="font-semibold text-sm mb-4 text-muted">Объявление {index + 1}</h3>

                    <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] gap-6">
                        {/* Image Upload */}
                        <div className="space-y-2">
                            <Label>Изображение</Label>
                            <div className="relative aspect-square rounded-lg border-2 border-dashed border-border flex flex-col items-center justify-center bg-black/20 hover:bg-black/30 transition-colors overflow-hidden">
                                {ad.image_url ? (
                                    <img src={ad.image_url} alt="Preview" className="w-full h-full object-cover" />
                                ) : (
                                    <div className="text-center p-4">
                                        <ImageIcon className="w-8 h-8 text-muted mx-auto mb-2 opacity-50" />
                                        <span className="text-xs text-muted block">{uploading === ad.id ? "Загрузка..." : "Загрузить"}</span>
                                    </div>
                                )}
                                <input
                                    type="file"
                                    className="absolute inset-0 opacity-0 cursor-pointer"
                                    onChange={(e) => handleFileChange(ad.id, e)}
                                    accept="image/*"
                                />
                            </div>
                        </div>

                        {/* Fields */}
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label>Заголовок</Label>
                                <Input
                                    value={ad.title}
                                    onChange={(e) => updateAd(ad.id, 'title', e.target.value)}
                                    placeholder="Купите слона сегодня"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Текст объявления</Label>
                                <Textarea
                                    value={ad.text}
                                    onChange={(e) => updateAd(ad.id, 'text', e.target.value)}
                                    placeholder="Лучшие слоны в городе. Скидки до 50%."
                                    className="h-20"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Ссылка</Label>
                                <Input
                                    value={ad.link}
                                    onChange={(e) => updateAd(ad.id, 'link', e.target.value)}
                                    placeholder="https://mysite.com/elephants"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            ))}

            <Button variant="outline" onClick={addAd} className="w-full border-dashed">
                <Plus className="w-4 h-4 mr-2" /> Добавить еще одно объявление
            </Button>
        </div>
    );
}
