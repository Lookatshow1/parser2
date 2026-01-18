"use client";

import { cn } from "@/lib/utils";

interface YandexPreviewProps {
    title: string;
    text: string;
    url?: string;
    sitelinks?: string[];
    className?: string;
}

/**
 * Предпросмотр объявления в стиле поисковой выдачи Яндекса
 */
export function YandexPreview({
    title,
    text,
    url = "example.ru",
    sitelinks = [],
    className
}: YandexPreviewProps) {
    return (
        <div className={cn(
            "bg-white rounded-lg p-4 font-sans text-left max-w-[600px]",
            className
        )}>
            {/* Domain */}
            <div className="flex items-center gap-2 mb-1">
                <div className="w-4 h-4 bg-gray-200 rounded-full flex items-center justify-center">
                    <span className="text-[8px] text-gray-500">Y</span>
                </div>
                <span className="text-sm text-gray-600">{url}</span>
                <span className="text-xs text-gray-400">• Реклама</span>
            </div>

            {/* Title */}
            <h3 className="text-[#1a0dab] text-lg font-normal hover:underline cursor-pointer mb-1 leading-tight">
                {title}
            </h3>

            {/* Description */}
            <p className="text-sm text-gray-700 leading-relaxed mb-2">
                {text}
            </p>

            {/* Sitelinks */}
            {sitelinks.length > 0 && (
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
                    {sitelinks.map((link, idx) => (
                        <a
                            key={idx}
                            href="#"
                            className="text-sm text-[#1a0dab] hover:underline"
                        >
                            {link}
                        </a>
                    ))}
                </div>
            )}
        </div>
    );
}

interface YandexBannerPreviewProps {
    title: string;
    text: string;
    imageUrl?: string;
    buttonText?: string;
    className?: string;
}

/**
 * Предпросмотр баннера РСЯ (Рекламная Сеть Яндекса)
 */
export function YandexBannerPreview({
    title,
    text,
    imageUrl,
    buttonText = "Подробнее",
    className
}: YandexBannerPreviewProps) {
    return (
        <div className={cn(
            "bg-white rounded-lg overflow-hidden shadow-lg max-w-[300px]",
            className
        )}>
            {/* Image */}
            <div className="h-[150px] bg-gradient-to-br from-purple-500 to-blue-600 relative">
                {imageUrl ? (
                    <img src={imageUrl} alt="" className="w-full h-full object-cover" />
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-white/50 text-sm">Изображение</span>
                    </div>
                )}
                <div className="absolute top-2 right-2 text-[10px] bg-black/30 text-white px-1.5 py-0.5 rounded">
                    Реклама
                </div>
            </div>

            {/* Content */}
            <div className="p-3">
                <h4 className="font-semibold text-gray-900 text-sm mb-1 line-clamp-2">
                    {title}
                </h4>
                <p className="text-xs text-gray-600 line-clamp-2 mb-3">
                    {text}
                </p>
                <button className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-medium text-sm py-2 rounded transition-colors">
                    {buttonText}
                </button>
            </div>
        </div>
    );
}
