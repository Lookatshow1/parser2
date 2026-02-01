"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { OAuthApi } from "../../../lib/api";
import { Card, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";

/**
 * OAuth Callback Page
 * 
 * Handles OAuth callback for Yandex Direct.
 * Yandex OAuth returns: ?code=...
 * 
 * For VK: handled manually via code paste on connections page.
 */
export default function OAuthCallbackPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [status, setStatus] = useState<"processing" | "success" | "error">("processing");
    const [message, setMessage] = useState("Обработка авторизации...");

    useEffect(() => {
        const code = searchParams.get("code");
        const state = searchParams.get("state");
        const error = searchParams.get("error");
        const errorDescription = searchParams.get("error_description");

        // Handle OAuth error
        if (error) {
            setStatus("error");
            setMessage(errorDescription || error || "Ошибка авторизации");
            toast.error(errorDescription || "Ошибка OAuth");
            return;
        }

        // Must have authorization code
        if (!code) {
            setStatus("error");
            setMessage("Код авторизации не получен");
            toast.error("Код авторизации отсутствует");
            return;
        }

        // Get platform from sessionStorage (set before redirect)
        const platform = sessionStorage.getItem("oauth_platform") || "yandex";

        // Exchange code for token and create connection
        const exchangeCode = async () => {
            try {
                const result = await OAuthApi.exchangeCode({
                    platform,
                    code,
                    state: state || undefined,
                });

                setStatus("success");
                setMessage(`Подключение создано: ${result.message}`);
                toast.success(result.message);

                // Clean up sessionStorage
                sessionStorage.removeItem("oauth_platform");

                // Redirect to connections after delay
                setTimeout(() => {
                    router.push("/connections");
                }, 2000);

            } catch (err) {
                setStatus("error");
                const errorMessage = (err as Error).message;
                setMessage(errorMessage);
                toast.error(errorMessage);
            }
        };

        exchangeCode();
    }, [searchParams, router]);

    return (
        <div className="flex min-h-screen items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardContent className="py-8 text-center">
                    {status === "processing" && (
                        <>
                            <div className="mb-4 flex justify-center">
                                <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                            </div>
                            <h2 className="text-xl font-semibold text-text">Подключение аккаунта</h2>
                            <p className="mt-2 text-muted">{message}</p>
                        </>
                    )}

                    {status === "success" && (
                        <>
                            <div className="mb-4 flex justify-center">
                                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-success/20 text-success">
                                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                </div>
                            </div>
                            <h2 className="text-xl font-semibold text-text">Успешно!</h2>
                            <p className="mt-2 text-muted">{message}</p>
                            <p className="mt-4 text-sm text-muted">Перенаправление на страницу подключений...</p>
                        </>
                    )}

                    {status === "error" && (
                        <>
                            <div className="mb-4 flex justify-center">
                                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-danger/20 text-danger">
                                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </div>
                            </div>
                            <h2 className="text-xl font-semibold text-text">Ошибка</h2>
                            <p className="mt-2 text-danger">{message}</p>
                            <Button
                                className="mt-6"
                                onClick={() => router.push("/connections")}
                            >
                                Вернуться к подключениям
                            </Button>
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
