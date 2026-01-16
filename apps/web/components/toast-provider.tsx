"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

interface ToastContextType {
    toasts: Toast[];
    addToast: (type: ToastType, message: string, duration?: number) => void;
    removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error("useToast must be used within ToastProvider");
    }
    return context;
}

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((type: ToastType, message: string, duration = 5000) => {
        const id = Math.random().toString(36).substring(7);
        const toast: Toast = { id, type, message, duration };

        setToasts(prev => [...prev, toast]);

        if (duration > 0) {
            setTimeout(() => {
                removeToast(id);
            }, duration);
        }
    }, []);

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </ToastContext.Provider>
    );
}

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: string) => void }) {
    if (toasts.length === 0) return null;

    return (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
            {toasts.map(toast => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
            ))}
        </div>
    );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
    const icons = {
        success: <CheckCircle className="h-5 w-5 text-green-400" />,
        error: <AlertCircle className="h-5 w-5 text-red-400" />,
        info: <Info className="h-5 w-5 text-blue-400" />,
        warning: <AlertTriangle className="h-5 w-5 text-yellow-400" />,
    };

    const bgColors = {
        success: "bg-green-900/80 border-green-500/30",
        error: "bg-red-900/80 border-red-500/30",
        info: "bg-blue-900/80 border-blue-500/30",
        warning: "bg-yellow-900/80 border-yellow-500/30",
    };

    return (
        <div className={`flex items-center gap-3 p-4 rounded-lg border backdrop-blur-sm shadow-lg ${bgColors[toast.type]} animate-slide-in`}>
            {icons[toast.type]}
            <p className="text-white text-sm flex-1">{toast.message}</p>
            <button onClick={() => onRemove(toast.id)} className="text-white/60 hover:text-white">
                <X className="h-4 w-4" />
            </button>
        </div>
    );
}
