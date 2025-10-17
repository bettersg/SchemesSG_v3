import { useChat } from "@/app/providers";
import { Button, Spinner, Textarea } from "@heroui/react";
import { FocusEvent, MutableRefObject, useState } from "react";
import { SearchIcon } from "../assets/icons/search-icon";
import { getSchemes } from "./main-chat";

interface SearchBarProps {
  searchbarRef: MutableRefObject<HTMLTextAreaElement | null>;
}
export default function SearchBar({ searchbarRef }: SearchBarProps) {
  const LABEL =
    "Let us know how we can help you. Please give us more details on which schemes best suit your needs.";
  const DESCRIPTION = "Please avoid providing identifiable information.";
  const PLACEHOLDER =
    "E.g. I am a cancer patient in need of financial assistance and food support.";

  const {
    setMessages,
    userQuery,
    setUserQuery,
    setSchemes,
    setSessionId,
    setTotalCount,
    setNextCursor,
  } = useChat();
  const [isBotResponseGenerating, setIsBotResponseGenerating] =
    useState<boolean>(false);

  const scrollToView = (e: FocusEvent<HTMLInputElement, Element>) => {
    if (e.target) {
      e.target.scrollIntoView({ behavior: "smooth", inline: "nearest" });
    }
  };

  const handleSend = async () => {
    if (userQuery.trim()) {
      setIsBotResponseGenerating(true);
      const { schemesRes, sessionId, totalCount, nextCursor } =
        await getSchemes(userQuery);
      setTotalCount(totalCount);
      setNextCursor(nextCursor);
      setUserQuery(userQuery);
      setIsBotResponseGenerating(false);

      // Always set sessionId if it exists, regardless of results
      if (sessionId !== "") {
        setSessionId(sessionId);
        setMessages([
          {
            type: "user",
            text: userQuery,
          },
        ]);
      }

      // Set schemes if we have results
      if (schemesRes.length > 0) {
        setSchemes(schemesRes);
      } else {
        // Clear schemes if no results but keep sessionId for chat
        setSchemes([]);
      }
    }
  };

  return (
    <>
      <Textarea
        value={userQuery}
        onChange={(e) => setUserQuery(e.target.value)}
        onFocus={scrollToView}
        onKeyDown={async (e) => {
          if (e.key === "Enter" && !isBotResponseGenerating) {
            e.preventDefault();
            await handleSend();
          }
        }}
        ref={searchbarRef}
        classNames={{
          input: "placeholder:italic placeholder:text-black/20",
          label: "font-semibold",
        }}
        type="text"
        size="md"
        radius="lg"
        color="primary"
        label={LABEL}
        labelPlacement="outside"
        description={DESCRIPTION}
        placeholder={PLACEHOLDER}
        endContent={
          <div className="flex items-end gap-2 h-full">
            {isBotResponseGenerating ? (
              <>
                <span className="text-xs text-gray-500 whitespace-nowrap">
                  Finding schemes...
                </span>
                <Spinner size="sm" className="mt-auto" />
              </>
            ) : (
              <Button
                color="primary"
                isIconOnly
                size="sm"
                radius="full"
                onPress={async () => await handleSend()}
                className="mt-auto"
              >
                <SearchIcon size={16} />
              </Button>
            )}
          </div>
        }
      />
    </>
  );
}
