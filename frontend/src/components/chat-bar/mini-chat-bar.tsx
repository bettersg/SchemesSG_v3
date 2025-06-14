import { SearchIcon } from "@/assets/icons/search-icon";
import { Button, Textarea } from "@nextui-org/react";
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
      <div className="py-2 px-8">
        <Textarea
          readOnly
          onClick={onExpand}
          placeholder="Please type your question"
          size="sm"
          radius="lg"
          color="primary"
          labelPlacement="outside"
          className="z-10 mt-auto"
          classNames={{
            input:"py-[0.3rem] placeholder:italic placeholder:text-black/20"
          }}
          endContent={
            <Button
              isIconOnly
              color="primary"
              size="sm"
              radius="full"
              onPress={onExpand}
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
