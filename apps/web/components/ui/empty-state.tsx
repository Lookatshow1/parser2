import { cn } from "../../lib/utils";
import { LucideIcon } from "lucide-react";
import { Button } from "./button";
import Link from "next/link";

type EmptyStateProps = {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  actionLabel?: string;
  actionHref?: string;
  secondaryLabel?: string;
  secondaryHref?: string;
  className?: string;
  tip?: string;
};

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  actionLabel,
  actionHref,
  secondaryLabel,
  secondaryHref,
  className,
  tip
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-2xl border border-border bg-panel px-8 py-12 text-center",
        className
      )}
    >
      {/* Icon */}
      {Icon && (
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent/20 to-fuchsia-500/20 flex items-center justify-center mb-2">
          <Icon className="h-8 w-8 text-accent" />
        </div>
      )}

      {/* Title */}
      <div className="text-lg font-semibold text-text">{title}</div>

      {/* Description */}
      {description && (
        <div className="max-w-md text-sm text-muted">{description}</div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
        {action}
        {actionLabel && actionHref && (
          <Button asChild>
            <Link href={actionHref}>{actionLabel}</Link>
          </Button>
        )}
        {secondaryLabel && secondaryHref && (
          <Button variant="outline" asChild>
            <Link href={secondaryHref}>{secondaryLabel}</Link>
          </Button>
        )}
      </div>

      {/* Tip */}
      {tip && (
        <div className="mt-4 p-3 bg-panel-strong/50 rounded-lg max-w-sm">
          <p className="text-xs text-muted">💡 {tip}</p>
        </div>
      )}
    </div>
  );
}
