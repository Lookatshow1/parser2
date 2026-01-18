"use client";

/**
 * Global Error Boundary for root layout errors
 * Required by Next.js App Router
 */

export default function GlobalError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    return (
        <html>
            <body style={{
                minHeight: "100vh",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#0a0a0f",
                color: "#fff",
                fontFamily: "system-ui, sans-serif"
            }}>
                <div style={{ textAlign: "center", padding: "2rem" }}>
                    <h1 style={{ fontSize: "2rem", marginBottom: "1rem" }}>
                        Что-то пошло не так
                    </h1>
                    <p style={{ color: "#888", marginBottom: "2rem" }}>
                        Произошла критическая ошибка
                    </p>
                    <button
                        onClick={() => reset()}
                        style={{
                            padding: "0.75rem 1.5rem",
                            backgroundColor: "#7c3aed",
                            color: "#fff",
                            border: "none",
                            borderRadius: "0.5rem",
                            cursor: "pointer",
                            fontSize: "1rem"
                        }}
                    >
                        Попробовать снова
                    </button>
                </div>
            </body>
        </html>
    );
}
