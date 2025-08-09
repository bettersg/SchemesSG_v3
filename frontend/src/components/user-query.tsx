import { useChat } from "@/app/providers";
import { ResetIcon } from "@/assets/icons/reset-icon";
import { EditIcon } from "@/assets/icons/edit-icon";
import { ConfirmIcon } from "@/assets/icons/confirm-icon";
import { CancelIcon } from "@/assets/icons/cancel-icon";
import { ButtonGroup, Card, CardBody, CardHeader, Input } from "@heroui/react";
import { Button, Tooltip, useDisclosure } from "@heroui/react";
import ResetQueryModal from "./reset-query-modal";
import clsx from "clsx";
import { useRef, useState } from "react";
import { getSchemes } from "./main-chat";

interface userQueryProps {
  resetFilters: () => void;
  setIsLoadingSchemes: (value: boolean) => void;
}

export default function UserQuery({
  resetFilters,
  setIsLoadingSchemes,
}: userQueryProps) {
  const { setSchemes, messages, setMessages, setSessionId, setTotalCount, setNextCursor, userQuery, setUserQuery } =
    useChat();
  const { isOpen, onOpen, onOpenChange } = useDisclosure();
  const firstMessage = messages[0].text;

  const inputRef = useRef<HTMLInputElement>(null);
  const [isEdit, setIsEdit] = useState(false);
  const handleReset = () => {
    sessionStorage.removeItem("schemes");
    sessionStorage.removeItem("userMessages");
    sessionStorage.removeItem("sessionID");
    sessionStorage.removeItem("userQuery");
    setSchemes([]);
    setMessages([]);
    setSessionId("");
    setUserQuery("");
    resetFilters();
  };
  const handleQueryChange = async () => {
    if (inputRef?.current?.value) {
      const queryValue = inputRef.current.value;
      const query = queryValue.trim();
      if (query != firstMessage) {
        setIsEdit(false);
        setUserQuery(query);
        setMessages([
          {
            type: "user",
            text: query,
          },
        ]);
        setIsLoadingSchemes(true);
        const { schemesRes, sessionId, totalCount, nextCursor } = await getSchemes(query);
        setTotalCount(totalCount)
        setNextCursor(nextCursor)
        if (schemesRes.length > 0 && sessionId !== "") {
          schemesRes && setSchemes(schemesRes);
          setSessionId(sessionId);
          resetFilters();
        }
        setIsLoadingSchemes(false);
      }
    }
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
        {!isEdit ? (
          <ButtonGroup variant="light" color="primary">
            <Tooltip content="Reset Query" offset={8}>
              <Button onPress={onOpen} isIconOnly radius="full">
                <ResetIcon />
              </Button>
            </Tooltip>
            <Tooltip content="Edit Query" offset={8}>
              <Button onPress={() => setIsEdit(true)} isIconOnly radius="full">
                <EditIcon />
              </Button>
            </Tooltip>
          </ButtonGroup>
        ) : (
          <ButtonGroup variant="light" color="primary">
            <Tooltip content="Confirm" offset={8}>
              <Button onPress={handleQueryChange} isIconOnly radius="full">
                <ConfirmIcon />
              </Button>
            </Tooltip>
            <Tooltip content="Cancel" offset={8}>
              <Button onPress={() => setIsEdit(false)} isIconOnly radius="full">
                <CancelIcon />
              </Button>
            </Tooltip>
          </ButtonGroup>
        )}
        <ResetQueryModal
          isOpen={isOpen}
          onOpenChange={onOpenChange}
          handleReset={handleReset}
        />
      </CardHeader>
      <CardBody className="px-2 py-1">
        {isEdit ? (
          <Input
            variant="bordered"
            defaultValue={firstMessage}
            onKeyDown={async (e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                await handleQueryChange();
              }
            }}
            ref={inputRef}
            autoFocus
          />
        ) : (
          <b>{userQuery}</b>
        )}
      </CardBody>
    </Card>
  );
}
