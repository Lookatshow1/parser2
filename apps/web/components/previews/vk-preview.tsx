"use client";

import { cn } from "@/lib/utils";
import { Heart, MessageCircle, Share2, MoreHorizontal } from "lucide-react";

interface VKPreviewProps {
    title: string;
    text: string;
    imageUrl?: string;
    buttonText?: string;
    advertiser?: string;
    className?: string;
}

/**
 * Предпросмотр рекламного поста в ленте VK
 */
export function VKPreview({
    title,
    text,
    imageUrl,
    buttonText = "Перейти",
    advertiser = "Рекламодатель",
    className
}: VKPreviewProps) {
    return (
        <div className={cn(
            "bg-white rounded-xl overflow-hidden shadow-lg max-w-[400px] font-sans",
            className
        )}>
            {/* Header */}
            <div className="p-3 flex items-center justify-between border-b border-gray-100">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <span className="text-white font-bold text-sm">
                            {advertiser.charAt(0).toUpperCase()}
                        </span>
                    </div>
                    <div>
                        <div className="font-semibold text-gray-900 text-sm">{advertiser}</div>
                        <div className="text-xs text-gray-500 flex items-center gap-1">
                            <span>Реклама</span>
                            <span>•</span>
                            <span>vk.com</span>
                        </div>
                    </div>
                </div>
                <button className="p-2 hover:bg-gray-100 rounded-full">
                    <MoreHorizontal className="w-5 h-5 text-gray-500" />
                </button>
            </div>

            {/* Content */}
            <div className="p-3">
                <p className="text-gray-900 text-sm leading-relaxed mb-2">
                    {text}
                </p>
            </div>

            {/* Image */}
            {(imageUrl || true) && (
                <div className="relative">
                    {imageUrl ? (
                        <img src={imageUrl} alt="" className="w-full h-[200px] object-cover" />
                    ) : (
                        <div className="w-full h-[200px] bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center">
                            <span className="text-white/60 text-sm">Изображение</span>
                        </div>
                    )}

                    {/* CTA Button overlay */}
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-4">
                        <h4 className="text-white font-semibold text-lg mb-2">{title}</h4>
                        <button className="bg-[#4C75A3] hover:bg-[#3d6285] text-white font-medium px-6 py-2 rounded-lg text-sm transition-colors">
                            {buttonText}
                        </button>
                    </div>
                </div>
            )}

            {/* Actions */}
            <div className="px-3 py-2 flex items-center gap-6 border-t border-gray-100">
                <button className="flex items-center gap-1.5 text-gray-500 hover:text-red-500 transition-colors">
                    <Heart className="w-5 h-5" />
                    <span className="text-sm">234</span>
                </button>
                <button className="flex items-center gap-1.5 text-gray-500 hover:text-blue-500 transition-colors">
                    <MessageCircle className="w-5 h-5" />
                    <span className="text-sm">18</span>
                </button>
                <button className="flex items-center gap-1.5 text-gray-500 hover:text-green-500 transition-colors">
                    <Share2 className="w-5 h-5" />
                    <span className="text-sm">12</span>
                </button>
            </div>
        </div>
    );
}

interface VKStoryPreviewProps {
    title: string;
    buttonText?: string;
    imageUrl?: string;
    className?: string;
}

/**
 * Предпросмотр рекламы в Stories VK
 */
export function VKStoryPreview({
    title,
    buttonText = "Подробнее",
    imageUrl,
    className
}: VKStoryPreviewProps) {
    return (
        <div className={cn(
            "relative w-[180px] h-[320px] rounded-2xl overflow-hidden shadow-lg",
            className
        )}>
            {/* Background */}
            {imageUrl ? (
                <img src={imageUrl} alt="" className="absolute inset-0 w-full h-full object-cover" />
            ) : (
                <div className="absolute inset-0 bg-gradient-to-br from-pink-500 via-red-500 to-orange-500" />
            )}

            {/* Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/20" />

            {/* Content */}
            <div className="absolute bottom-0 left-0 right-0 p-3">
                <p className="text-white text-sm font-medium mb-2 line-clamp-2">{title}</p>
                <button className="w-full bg-white/90 hover:bg-white text-gray-900 font-medium py-2 rounded-lg text-sm transition-colors">
                    {buttonText}
                </button>
            </div>

            {/* Progress bar */}
            <div className="absolute top-2 left-2 right-2 h-0.5 bg-white/30 rounded-full overflow-hidden">
                <div className="w-1/3 h-full bg-white rounded-full" />
            </div>

            {/* Ad label */}
            <div className="absolute top-4 left-2 text-[10px] bg-black/40 text-white px-2 py-0.5 rounded">
                Реклама
            </div>
        </div>
    );
}
