import {
  productPageShell,
  productPageContent,
  productFormContent,
} from "@/lib/design-system/product-styles";
import { cn } from "@/lib/utils";

type PageShellProps = {
  children: React.ReactNode;
  width?: "default" | "form";
  className?: string;
  contentClassName?: string;
};

export default function PageShell({
  children,
  width = "default",
  className,
  contentClassName,
}: PageShellProps) {
  const content = width === "form" ? productFormContent : productPageContent;
  return (
    <div className={cn(productPageShell, className)}>
      <div className={cn(content, contentClassName)}>{children}</div>
    </div>
  );
}
