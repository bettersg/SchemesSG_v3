import {
  productButtonCompact,
  productButtonOutlineBlue,
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
      className={`${productButtonOutlineBlue} ${productButtonCompact} aspect-square shrink-0 px-0 sm:aspect-auto sm:w-auto sm:px-3`}
      onPress={onPress}
    >
      <span className="max-sm:hidden sm:block">New chat</span>
      <RotateCcw className="max-sm:block sm:hidden" />
    </Button>
  );
}
