import { Button, Spinner, Textarea } from "@heroui/react";
import { SendIcon } from "../../assets/icons/send-icon";
import QuerySuggestions from "../query-suggestions/query-suggestions";
import { useEffect, useRef } from "react";

interface ChatBarProps {
  userInput: string;
  setUserInput: React.Dispatch<React.SetStateAction<string>>;
  handleUserInput: (message: string) => void;
  isBotResponseGenerating: boolean;
}

export default function ChatBar({
  userInput,
  setUserInput,
  handleUserInput,
  isBotResponseGenerating,
}: ChatBarProps) {
  const handleSend = () => {
    if (userInput.trim()) {
      handleUserInput(userInput);
    }
    setUserInput("");
  };

  const handleSetInput = (input: string) => {
    setUserInput(input);
  };

  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  return (
    <Textarea
      ref={inputRef}
      value={userInput}
      onChange={(e) => setUserInput(e.target.value)}
      onKeyDown={async (e) => {
        if (e.key === "Enter" && !isBotResponseGenerating) {
          e.preventDefault();
          handleSend();
        }
      }}
      className="z-10 border-solid border-2 border-primary-100 rounded-2xl"
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
        <div className="flex items-center">
          <QuerySuggestions setUserInput={handleSetInput} />
        </div>
      }
      endContent={
        isBotResponseGenerating ? (
          <Spinner className="mt-auto" size="sm" />
        ) : (
          <Button
            className="mt-auto"
            color="primary"
            isIconOnly
            size="md"
            radius="full"
            onPress={handleSend}
          >
            <SendIcon size={16} />
          </Button>
        )
      }
    />
  );
}
