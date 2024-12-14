"use client";

import { useState, useEffect } from "react";
import { Button, Spinner, Textarea } from "@nextui-org/react";
import { SearchIcon } from "../../assets/icons/search-icon";
import classes from "./search-bar.module.css";
import { useChat } from "@/app/providers";

interface SearchBarProps {
  setSessionId: (val: string) => void;
  selectedSupportProvided: string | null;
  selectedForWho: string | null;
  selectedOrganisation: string | null;
}

export default function SearchBar({
  setSessionId,
  selectedSupportProvided,
  selectedForWho,
  selectedOrganisation,
}: SearchBarProps) {
  const { setMessages, setUserQuery, setSchemes } = useChat();
  const [userInput, setUserInput] = useState("");
  const [isBotResponseGenerating, setIsBotResponseGenerating] =
    useState<boolean>(false);

  useEffect(() => {
    let query = "I am looking for";

    if (selectedSupportProvided) {
      query += ` ${selectedSupportProvided}`;
    }

    if (selectedForWho) {
      query += selectedSupportProvided
        ? ` for ${selectedForWho}`
        : ` schemes for ${selectedForWho}`;
    }

    if (selectedOrganisation) {
      query +=
        selectedSupportProvided || selectedForWho
          ? ` from ${selectedOrganisation}`
          : ` schemes from ${selectedOrganisation}`;
    }

    // Default to empty if no filters are selected
    setUserInput(query === "I am looking for" ? "" : query);
  }, [selectedSupportProvided, selectedForWho, selectedOrganisation]);

  const handleUserInput = (input: string) => {
    setMessages([
      {
        type: "user",
        text: input,
      },
    ]);
    setUserQuery(input);
    setUserInput("");
  };

  return (
    <>
      <Textarea
        value={userInput}
        onChange={(e) => setUserInput(e.target.value)}
        onKeyDown={async (e) => {
          if (e.key === "Enter" && !isBotResponseGenerating) {
            e.preventDefault();
            await handleUserInput(userInput);
          }
        }}
        className={classes.searchBar}
        type="text"
        size="md"
        radius="lg"
        color="primary"
        label="How can we help?"
        labelPlacement="outside"
        description="Please avoid providing identifiable information."
        placeholder="E.g. I am a dialysis patient in need of financial assistance and food support."
        endContent={
          isBotResponseGenerating ? (
            <Spinner className={classes.endContent} size="sm" />
          ) : (
            <Button
              className={classes.endContent}
              isIconOnly
              size="sm"
              radius="full"
              onClick={async () => await handleUserInput(userInput)}
            >
              <SearchIcon />
            </Button>
          )
        }
      />
    </>
  );
}
