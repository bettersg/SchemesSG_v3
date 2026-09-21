import {
  productCard,
  productCardPadded,
} from "@/lib/design-system/product-styles";
import { cn } from "@/lib/utils";

type CardProps = React.HTMLAttributes<HTMLDivElement> & {
  padded?: boolean;
};

export default function Card({
  padded = true,
  className,
  children,
  ...rest
}: CardProps) {
  return (
    <div
      className={cn(padded ? productCardPadded : productCard, className)}
      {...rest}
    >
      {children}
    </div>
  );
}
