import { useChat } from "@/app/providers";
import { ResetIcon } from "@/assets/icons/reset-icon";
import { Card, CardBody, CardHeader } from "@heroui/react";
import { Button, Tooltip, useDisclosure } from "@heroui/react";
import ResetQueryModal from "./reset-query-modal";
import clsx from "clsx";

export default function UserQuery({
  resetFilters,
}: {
  resetFilters: () => void;
}) {
  const { setSchemes, messages, setMessages, setSessionId, setUserQuery } =
    useChat();
  const { isOpen, onOpen, onOpenChange } = useDisclosure();
  const firstMessage = messages[0].text;
  const handleReset = () => {
    localStorage.removeItem("schemes");
    localStorage.removeItem("userMessages");
    localStorage.removeItem("sessionID");
    localStorage.removeItem("userQuery");
    setSchemes([]);
    setMessages([]);
    setSessionId("");
    setUserQuery("");
    resetFilters();
  };

  return (
    <Card
      className={clsx(
        "w-full sm:w-[95%] p-[3px] my-2 sm:mx-2",
        "rounded-2xl text-sm",
        "bg-white"
      )}
      fullWidth={false}
      radius="lg"
      shadow="none"
    >
      <CardHeader className="justify-between px-2 py-1">
        <h4 className="text-small leading-none text-default-600">
          Your query is:
        </h4>
        <Tooltip content="Reset Query" offset={-7}>
          <Button
            onPress={onOpen}
            isIconOnly
            radius="full"
            size="sm"
            className="bg-transparent w-6 h-6"
          >
            <ResetIcon />
          </Button>
        </Tooltip>
        <ResetQueryModal
          isOpen={isOpen}
          onOpenChange={onOpenChange}
          handleReset={handleReset}
        />
      </CardHeader>
      <CardBody className="px-2 py-1">
        <b>{firstMessage}</b>
      </CardBody>
    </Card>
  );
}
