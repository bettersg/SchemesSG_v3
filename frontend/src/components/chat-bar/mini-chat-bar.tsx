import { InfoIcon } from "@/assets/icons/info-icon";
import { SendIcon } from "@/assets/icons/send-icon";
import { Button, Textarea } from "@heroui/react";
import clsx from "clsx";
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
      className={clsx(
        "absolute bottom-0 left-0 right-0 bg-none",
        isExpanded ? "hidden" : "block"
      )}
    >
      <div className="py-2 px-8">
        <Textarea
          readOnly
          onClick={onExpand}
          className="z-10 mt-auto border-solid border-2 border-primary-100 rounded-2xl"
          classNames={{
            input: "py-[0.3rem] placeholder:italic placeholder:text-black/20",
          }}
          type="text"
          size="md"
          radius="lg"
          color="primary"
          labelPlacement="outside"
          placeholder="Please type your follow-up question"
          startContent={
            <div className="flex items-center invisible">
              <Button
                isIconOnly
                size="sm"
                variant="light"
                className="text-schemes-darkgray hover:text-schemes-darkblue"
              >
                <InfoIcon size={16} />
              </Button>
            </div>
          }
          endContent={
            <Button
              className="mt-auto"
              color="primary"
              isIconOnly
              size="md"
              radius="full"
            >
              <SendIcon size={16}/>
            </Button>
          }
        />
      </div>
    </div>
  );
}
