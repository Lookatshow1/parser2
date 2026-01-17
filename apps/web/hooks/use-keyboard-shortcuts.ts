/**
 * Keyboard Shortcuts Hook
 *
 * Global keyboard shortcuts for the application.
 */

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

interface ShortcutConfig {
    key: string;
    ctrl?: boolean;
    meta?: boolean;
    shift?: boolean;
    alt?: boolean;
    action: () => void;
    description: string;
}

export function useKeyboardShortcuts(shortcuts: ShortcutConfig[]) {
    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            for (const shortcut of shortcuts) {
                const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();
                const ctrlMatch = shortcut.ctrl ? event.ctrlKey : !event.ctrlKey;
                const metaMatch = shortcut.meta ? event.metaKey : !event.metaKey;
                const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
                const altMatch = shortcut.alt ? event.altKey : !event.altKey;

                if (keyMatch && ctrlMatch && metaMatch && shiftMatch && altMatch) {
                    event.preventDefault();
                    shortcut.action();
                    return;
                }
            }
        },
        [shortcuts]
    );

    useEffect(() => {
        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [handleKeyDown]);
}

/**
 * Default app shortcuts hook
 */
export function useAppShortcuts() {
    const router = useRouter();

    useKeyboardShortcuts([
        {
            key: "d",
            meta: true,
            action: () => router.push("/dashboard"),
            description: "Go to Dashboard",
        },
        {
            key: "m",
            meta: true,
            action: () => router.push("/magic"),
            description: "Go to Magic Create",
        },
        {
            key: "a",
            meta: true,
            shift: true,
            action: () => router.push("/analytics"),
            description: "Go to Analytics",
        },
        {
            key: "s",
            meta: true,
            shift: true,
            action: () => router.push("/settings"),
            description: "Go to Settings",
        },
        {
            key: "Escape",
            action: () => {
                // Close any open modals
                const event = new CustomEvent("closeModals");
                document.dispatchEvent(event);
            },
            description: "Close modals",
        },
    ]);
}
