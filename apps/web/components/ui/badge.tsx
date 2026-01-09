import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "border-slate-700 text-slate-200",
        success: "border-emerald-500/40 text-emerald-300",
        warning: "border-amber-500/40 text-amber-300",
        danger: "border-red-500/40 text-red-300",
        info: "border-blue-500/40 text-blue-300",
        muted: "border-slate-800 text-slate-400"
      }
    },
    defaultVariants: { variant: "default" }
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

