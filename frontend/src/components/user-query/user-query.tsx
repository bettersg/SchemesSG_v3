import { useChat } from "@/app/providers";
import { ResetIcon } from "@/assets/icons/reset-icon";
import { Card, CardBody, CardHeader } from "@nextui-org/card";
import { Button, Tooltip, useDisclosure } from "@nextui-org/react";
import ResetQueryModal from "../reset-query-modal/reset-query-modal";
import classes from "./user-query.module.css";

export default function UserQuery({ resetFilters }: { resetFilters: () => void }) {
  const { setSchemes, messages, setMessages, setSessionId, setUserQuery } = useChat();
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
      className={`${classes.card} ${classes.userQuery}`}
      fullWidth={false}
      radius="lg"
      shadow="none"
    >
      <CardHeader className={`justify-between ${classes.cardHeader}`}>
        <h4 className="text-small leading-none text-default-600">
          Your query is:
        </h4>
        <Tooltip content="Reset Query" offset={-7}>
          <Button
            onPress={onOpen}
            isIconOnly
            radius="full"
            size="sm"
            className={`${classes.resetButton}`}
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
      <CardBody className={`${classes.cardBody}`}>
        <b>{firstMessage}</b>
      </CardBody>
    </Card>
  );
}
