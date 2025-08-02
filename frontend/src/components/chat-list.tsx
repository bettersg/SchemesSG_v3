import { Avatar, Card, CardBody } from "@heroui/react";
import ReactMarkdown from "react-markdown";
import { Message } from "@/app/providers";
import { RefObject } from "react";
import clsx from "clsx";

interface ChatListProps {
  messages: Message[];
  streamingMessage?: string;
  scrollableDivRef: RefObject<HTMLDivElement>;
}

export default function ChatList({
  messages,
  streamingMessage,
  scrollableDivRef,
}: ChatListProps) {

  return (
    <div
      className={clsx(
        "chatList",
        "flex flex-col gap-2",
        "p-4 overflow-y-auto max-h-[65vh] sm:max-h-[68vh]"
      )}
      ref={scrollableDivRef}
    >
      {messages.map((msg, index) => (
        <div
          key={index}
          className={clsx(
            "messageContainer flex",
            msg.type === "user" ? "justify-end" : "justify-start"
          )}
        >
          {msg.type === "bot" && <Avatar name="S" size="sm" className="mr-2" />}
          <Card
            className={clsx(
              "max-w-[80%] p-[3px] rounded-2xl",
              "text-sm break-words",
              "bg-white",
              msg.type === "user" ? "text-schemes-blue self-end" : "self-start"
            )}
            fullWidth={false}
            radius="lg"
            shadow="none"
          >
            <CardBody className="px-2 py-1">
              <ReactMarkdown>{msg.text}</ReactMarkdown>
            </CardBody>
          </Card>
        </div>
      ))}

      {/* Streaming message */}
      {streamingMessage && (
        <div className="flex">
          <Avatar name="S" size="sm" className="mr-2" />
          <Card
            className={clsx(
              "max-w-[80%] p-[3px] rounded-2xl",
              "text-sm break-words",
              "bg-schemes-lightgray self-start"
            )}
            fullWidth={false}
            radius="lg"
            shadow="none"
          >
            <CardBody className="px-2 py-1">
              <ReactMarkdown>{streamingMessage}</ReactMarkdown>
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
}
