import { useChat } from "@/app/providers";
import { ResetIcon } from "@/assets/icons/reset-icon";
import { Card, CardBody, CardHeader } from "@nextui-org/card";
import { Button, Tooltip, useDisclosure } from "@nextui-org/react";
import ResetQueryModal from "../reset-query-modal/reset-query-modal";
import classes from "./user-query.module.css";

export default function UserQuery() {
  const { userQuery, setSchemes, setUserQuery } = useChat();
  const { isOpen, onOpen, onOpenChange } = useDisclosure();

  const handleReset = () => {
    localStorage.removeItem("schemes");
    localStorage.removeItem("userQuery");
    setSchemes([]);
    setUserQuery("");
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
        <b>{userQuery}</b>
      </CardBody>
    </Card>
  );
}
