import { cn } from "../../lib/utils";

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
};

export function EmptyState({ title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-2xl border border-border bg-panel px-6 py-10 text-center",
        className
      )}
    >
      <div className="text-base font-semibold text-text">{title}</div>
      {description ? <div className="max-w-md text-sm text-muted">{description}</div> : null}
      {action ? <div className="pt-2">{action}</div> : null}
    </div>
  );
}
