'use client';

import { Button, Spinner, Textarea } from "@nextui-org/react";
import { SearchIcon } from '../../assets/icons/search-icon';
import classes from './search-bar.module.css';
import { useState } from "react";
import { useChat } from "@/app/providers";

interface SearchBarProps {
    setIsSchemeListShown: (val: boolean) => void
}

export default function SearchBar({ setIsSchemeListShown }: SearchBarProps) {
    const { messages, setMessages } = useChat();
    const [userInput, setUserInput] = useState("");
    const [isBotResponseGenerating, setIsBotResponseGenerating] = useState<boolean>(false);

    const handleUserInput = (input: string) => {
        setMessages([...messages,
            { type: "user", text: input }
        ]);
        setUserInput("");
    };

    //TODO: Change bot response simulation to backend API
    const simulateBotResponse = (userMessage: string) => {
      setIsBotResponseGenerating(true);
      setTimeout(() => {
        const botReply = `Bot response to: ${userMessage}`;
        // handleBotResponse(botReply);
        setIsBotResponseGenerating(false);
        setIsSchemeListShown(true);
      }, 1000);
    };

    const handleSend = () => {
        if (userInput.trim()) {
          handleUserInput(userInput);
        //   simulateBotResponse(userInput);
        }
    };

    return (
        <>
            <Textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                className={classes.searchBar}
                type="text"
                size="md"
                radius="lg"
                color="primary"
                label="How can we help?"
                labelPlacement="outside"
                description="Please avoid providing identifiable information."
                placeholder="I am a dialysis patient in need of financial assistance and food support after being retrenched due to Covid-19."
                endContent={
                    isBotResponseGenerating
                    ? <Spinner className={classes.endContent} size="sm" />
                    : <Button className={classes.endContent} isIconOnly size="sm" radius="full" onClick={handleSend}>
                        <SearchIcon />
                    </Button>
                }
            />
        </>
    )
}
