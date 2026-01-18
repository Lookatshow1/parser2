"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface SwitchProps extends React.InputHTMLAttributes<HTMLInputElement> {
    onCheckedChange?: (checked: boolean) => void;
}

const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
    ({ className, onCheckedChange, checked, ...props }, ref) => {
        const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
            onCheckedChange?.(e.target.checked);
        };

        return (
            <label className="relative inline-flex items-center cursor-pointer">
                <input
                    type="checkbox"
                    ref={ref}
                    checked={checked}
                    onChange={handleChange}
                    className="sr-only peer"
                    {...props}
                />
                <div
                    className={cn(
                        "relative w-11 h-6 rounded-full transition-colors",
                        "bg-panel-strong border border-border",
                        "peer-checked:bg-accent peer-checked:border-accent",
                        "peer-focus-visible:outline-none peer-focus-visible:ring-2 peer-focus-visible:ring-accent peer-focus-visible:ring-offset-2",
                        "peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
                        className
                    )}
                >
                    <span
                        className={cn(
                            "absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-sm",
                            checked && "translate-x-5"
                        )}
                    />
                </div>
            </label>
        );
    }
);
Switch.displayName = "Switch";

export { Switch };
