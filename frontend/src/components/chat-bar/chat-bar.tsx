import { Button, Spinner, Textarea } from "@nextui-org/react";
import { SendIcon } from "../../assets/icons/send-icon";
import QuerySuggestions from "../query-suggestions/query-suggestions";

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

  return (
    <>
      <Textarea
        value={userInput}
        onChange={(e) => setUserInput(e.target.value)}
        onKeyDown={async (e) => {
          if (e.key === "Enter" && !isBotResponseGenerating) {
            e.preventDefault();
            handleSend();
          }
        }}
        className="z-10 mt-auto border-solid border-2 border-primary-100 rounded-2xl"
        classNames={{
          input:"py-[0.3rem] placeholder:italic placeholder:text-black/20"
        }}
        type="text"
        size="md"
        radius="lg"
        color="primary"
        labelPlacement="outside"
        placeholder="Please type your question"
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
              size="sm"
              radius="full"
              onPress={handleSend}
            >
              <SendIcon />
            </Button>
          )
        }
      />
    </>
  );
}
