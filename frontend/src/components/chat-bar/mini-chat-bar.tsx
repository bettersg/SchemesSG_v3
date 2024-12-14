import { SearchIcon } from "@/assets/icons/search-icon";
import { Button, Textarea } from "@nextui-org/react";
import classes from "./chat-bar.module.css";
interface MiniChatBarProps {
  onExpand: () => void;
  isExpanded: boolean;
}

export default function MiniChatBar({
  onExpand,
  isExpanded,
}: MiniChatBarProps) {
  return (
    <div
      className={`absolute bottom-0 left-0 right-0 bg-none
        ${isExpanded ? "hidden" : "block"}`}
    >
      <div className="p-4">
        <Textarea
          readOnly
          onClick={onExpand}
          placeholder="Please type your question"
          size="sm"
          radius="lg"
          color="primary"
          labelPlacement="outside"
          className={classes.chatBar}
          endContent={
            <Button
              isIconOnly
              size="sm"
              radius="full"
              onClick={onExpand}
              className="min-w-unit-8 w-unit-8 h-unit-8 self-end"
            >
              <SearchIcon />
            </Button>
          }
        />
      </div>
    </div>
  );
}
