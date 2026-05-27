import {
  productButtonSecondary,
  productButtonSm,
} from "@/lib/design-system/product-styles";
import { Button, PressEvent } from "@heroui/react";
import { RotateCcw } from "lucide-react";

interface NewChatButtonProps {
  onPress: ((e: PressEvent) => void) | undefined;
}

export default function NewChatButton({ onPress }: NewChatButtonProps) {
  return (
    <Button
      size="sm"
      variant="outline"
      className={`${productButtonSecondary} ${productButtonSm} shrink-0`}
      onPress={onPress}
    >
      <span className="max-sm:hidden sm:block">New chat</span>
      <RotateCcw className="max-sm:block sm:hidden" />
    </Button>
  );
}
