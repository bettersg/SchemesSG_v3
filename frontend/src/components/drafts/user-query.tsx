"use client";
import { useChat } from "@/providers";
import { ResetIcon } from "@/assets/icons/reset-icon";
import { EditIcon } from "@/assets/icons/edit-icon";
import { ConfirmIcon } from "@/assets/icons/confirm-icon";
import { CancelIcon } from "@/assets/icons/cancel-icon";
import { Button, ButtonGroup, Card, Input, Tooltip } from "@heroui/react";
import ResetQueryModal from "../reset-query-modal";
import clsx from "clsx";
import { useRef, useState } from "react";
import { getSchemes } from "@/lib/schemes";

interface userQueryProps {
  resetFilters: () => void;
  setIsLoadingSchemes: (value: boolean) => void;
}

export default function UserQuery({ resetFilters, setIsLoadingSchemes }: userQueryProps) {
  const { setSchemes, messages, setMessages, setSessionId, setTotalCount, setNextCursor, userQuery, setUserQuery } =
    useChat();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const firstMessage = messages[0].text;

  const inputRef = useRef<HTMLInputElement>(null);
  const [isEdit, setIsEdit] = useState(false);

  const handleReset = () => {
    sessionStorage.removeItem("schemes");
    sessionStorage.removeItem("userMessages");
    sessionStorage.removeItem("sessionID");
    sessionStorage.removeItem("userQuery");
    sessionStorage.removeItem("totalCount");
    sessionStorage.removeItem("nextCursor");
    setSchemes([]);
    setMessages([]);
    setSessionId("");
    setUserQuery("");
    setTotalCount(0);
    setNextCursor("");
    resetFilters();
    setIsModalOpen(false);
  };

  const handleQueryChange = async () => {
    if (inputRef?.current?.value) {
      const query = inputRef.current.value.trim();
      if (query !== firstMessage) {
        setIsEdit(false);
        setUserQuery(query);
        setMessages([{ type: "user", text: query }]);
        setIsLoadingSchemes(true);
        const { schemesRes, sessionId, totalCount, nextCursor } = await getSchemes(query);
        setTotalCount(totalCount);
        setNextCursor(nextCursor);
        if (sessionId !== "") setSessionId(sessionId);
        if (schemesRes.length > 0) {
          setSchemes(schemesRes);
          resetFilters();
        } else {
          setSchemes([]);
        }
        setIsLoadingSchemes(false);
      } else {
        setIsEdit(false);
      }
    }
  };

  return (
    <Card
      className={clsx(
        "w-full sm:w-[95%] p-[3px] my-2 sm:mx-2",
        "rounded-2xl text-sm shrink-0",
        "bg-white"
      )}
      shadow="none"
    >
      <Card.Header className="justify-between px-2 py-1">
        <h4 className="text-small leading-none text-default-600">Your query is:</h4>
        {!isEdit ? (
          <ButtonGroup variant="light" color="primary">
            <Tooltip delay={0}>
              <Tooltip.Trigger>
                <Button onPress={() => setIsModalOpen(true)} isIconOnly radius="full">
                  <ResetIcon />
                </Button>
              </Tooltip.Trigger>
              <Tooltip.Content>
                <p>Reset Query</p>
              </Tooltip.Content>
            </Tooltip>
            <Tooltip delay={0}>
              <Tooltip.Trigger>
                <Button onPress={() => setIsEdit(true)} isIconOnly radius="full">
                  <EditIcon />
                </Button>
              </Tooltip.Trigger>
              <Tooltip.Content>
                <p>Edit Query</p>
              </Tooltip.Content>
            </Tooltip>
          </ButtonGroup>
        ) : (
          <ButtonGroup variant="light" color="primary">
            <Tooltip delay={0}>
              <Tooltip.Trigger>
                <Button onPress={handleQueryChange} isIconOnly radius="full">
                  <ConfirmIcon />
                </Button>
              </Tooltip.Trigger>
              <Tooltip.Content>
                <p>Confirm</p>
              </Tooltip.Content>
            </Tooltip>
            <Tooltip delay={0}>
              <Tooltip.Trigger>
                <Button onPress={() => setIsEdit(false)} isIconOnly radius="full">
                  <CancelIcon />
                </Button>
              </Tooltip.Trigger>
              <Tooltip.Content>
                <p>Cancel</p>
              </Tooltip.Content>
            </Tooltip>
          </ButtonGroup>
        )}
        <ResetQueryModal
          isOpen={isModalOpen}
          onOpenChange={setIsModalOpen}
          handleReset={handleReset}
        />
      </Card.Header>
      <Card.Content className="px-2 py-1">
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
      </Card.Content>
    </Card>
  );
}
