import { Button, PressEvent } from "@heroui/react";
import { RotateCcw } from "lucide-react";

interface NewChatButtonProps {
  onPress: ((e: PressEvent) => void) | undefined;
}

// Quiet, borderless session reset. Deliberately NOT pill-shaped so it reads as
// a distinct action, not a third filter chip next to the Location/Agency pills.
export default function NewChatButton({ onPress }: NewChatButtonProps) {
  return (
    <Button
      size="sm"
      variant="ghost"
      className="inline-flex min-h-9 shrink-0 items-center gap-1.5 rounded-md border-0 bg-transparent px-2 text-xs font-semibold text-(--schemes-muted) transition-colors hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-600)"
      onPress={onPress}
    >
      <RotateCcw className="h-4! w-4! shrink-0" strokeWidth={2} />
      <span>New chat</span>
    </Button>
  );
}
