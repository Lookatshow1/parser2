"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
    onCheckedChange?: (checked: boolean) => void;
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
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
                        "h-4 w-4 shrink-0 rounded border border-border bg-panel-strong transition-colors",
                        "peer-focus-visible:outline-none peer-focus-visible:ring-2 peer-focus-visible:ring-accent peer-focus-visible:ring-offset-2",
                        "peer-checked:border-accent peer-checked:bg-accent",
                        "peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
                        className
                    )}
                >
                    {checked && (
                        <Check className="h-3 w-3 text-white m-auto" strokeWidth={3} />
                    )}
                </div>
            </label>
        );
    }
);
Checkbox.displayName = "Checkbox";

export { Checkbox };
