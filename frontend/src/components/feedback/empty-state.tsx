import { cn } from "@/lib/utils";

type EmptyStateProps = {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
};

export default function EmptyState({
  title,
  description,
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-20 text-center text-(--schemes-muted)",
        className,
      )}
    >
      {icon ? <div className="mb-3 text-(--schemes-blue-400)">{icon}</div> : null}
      <p className="mb-2 text-lg font-semibold text-(--schemes-ink-soft)">
        {title}
      </p>
      {description ? <p className="text-sm">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
