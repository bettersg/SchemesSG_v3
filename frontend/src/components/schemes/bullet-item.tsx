import { ReactNode } from "react";

interface BulletItemProps {
  children: ReactNode;
}

export default function BulletItem({ children }: BulletItemProps) {
  return (
    <div className="flex items-start gap-2.5 text-sm text-(--schemes-ink-soft)">
      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-(--schemes-muted)" />
      <span className="leading-snug">{children}</span>
    </div>
  );
}
