import { useChat, useSchemes } from "@/providers";
import { Button, TextArea, Label, TextField } from "@heroui/react";
import { Spinner } from "@heroui/react";

import { MutableRefObject, useState } from "react";
import { Search } from "lucide-react";
import {
  productButtonPrimary,
  productIconButton,
  productInputText,
} from "@/lib/design-system/product-styles";

interface QueryBarProps {
  searchbarRef: MutableRefObject<HTMLTextAreaElement | null>;
}
export default function QueryBar({ searchbarRef }: QueryBarProps) {
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
  } = useSchemes();
  const [isBotResponseGenerating, setIsBotResponseGenerating] =
    useState<boolean>(false);

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
      <TextField>
        <Label className="text-base md:text-lg font-semibold text-(--schemes-blue-900)">
          {LABEL}
        </Label>
        <TextArea
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          onKeyDown={async (e) => {
            if (e.key === "Enter" && !isBotResponseGenerating) {
              e.preventDefault();
              await handleSend();
            }
          }}
          ref={searchbarRef}
          placeholder={PLACEHOLDER}
          className={`${productInputText} text-base`}
        />
        <p className="text-base text-(--schemes-muted)">{DESCRIPTION}</p>
        <div className="mt-2 flex justify-end gap-2">
          {isBotResponseGenerating ? (
            <>
              <span className="text-xs text-(--schemes-muted) whitespace-nowrap">
                Finding schemes...
              </span>
              <Spinner size="sm" />
            </>
          ) : (
            <Button
              variant="primary"
              isIconOnly
              size="sm"
              onPress={async () => await handleSend()}
              className={`${productButtonPrimary} ${productIconButton}`}
            >
              <Search size={16} strokeWidth={2} />
            </Button>
          )}
        </div>
      </TextField>
    </>
  );
}
