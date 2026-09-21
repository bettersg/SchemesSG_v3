import { ReactNode } from "react";
import { AlertTriangle, Info } from "lucide-react";

type Variant = "info" | "alert";

interface StatusBannerProps {
  variant?: Variant;
  icon?: ReactNode;
  title?: string;
  className?: string;
  children: ReactNode;
}

const VARIANT_CLASSES: Record<Variant, { wrapper: string; iconColor: string; titleColor: string }> = {
  info: {
    wrapper:
      "rounded-xl border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-4",
    iconColor: "text-(--schemes-status-info-text)",
    titleColor: "text-(--schemes-status-info-text)",
  },
  alert: {
    wrapper:
      "rounded-xl border border-(--schemes-status-alert-border) bg-(--schemes-status-alert-bg) p-4",
    iconColor: "text-(--schemes-status-alert-text)",
    titleColor: "text-(--schemes-status-alert-text)",
  },
};

export default function StatusBanner({
  variant = "info",
  icon,
  title,
  className,
  children,
}: StatusBannerProps) {
  const v = VARIANT_CLASSES[variant];
  const defaultIcon =
    variant === "alert" ? (
      <AlertTriangle size={18} strokeWidth={2} className={`mt-0.5 shrink-0 ${v.iconColor}`} />
    ) : (
      <Info size={18} strokeWidth={2} className={`mt-0.5 shrink-0 ${v.iconColor}`} />
    );

  return (
    <section className={`${v.wrapper} ${className ?? ""}`}>
      <div className="flex items-start gap-4">
        {icon ?? defaultIcon}
        <div className="flex flex-col gap-2">
          {title && (
            <h3 className={`text-sm font-semibold ${v.titleColor}`}>
              {title}
            </h3>
          )}
          <div className="text-sm leading-relaxed text-(--schemes-muted)">
            {children}
          </div>
        </div>
      </div>
    </section>
  );
}
