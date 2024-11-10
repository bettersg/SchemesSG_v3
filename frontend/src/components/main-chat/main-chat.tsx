'use client';

import { useState } from "react";
import ChatList from "@/components/chat-list/chat-list";
import SearchBar from "@/components/search-bar/search-bar";
import { Spacer } from "@nextui-org/react";
import classes from "./main-chat.module.css"

export type Message = {
    type: "user" | "bot",
    text: string
}

export default function MainChat() {
    const [messages, setMessages] = useState<Message[]>([
        { type: "bot", text: "Hello! How can I help you today?" }
    ]);
    const [userInput, setUserInput] = useState("");
    const [botResponse, setBotResponse] = useState("");
    const [isBotResponseGenerating, setIsBotResponseGenerating] = useState<boolean>(false);

    const handleUserInput = (input: string) => {
        setMessages((prevMessages) => [
            ...prevMessages,
            { type: "user", text: input }
        ]);
        setUserInput("");
    };

    const handleBotResponse = (response: string) => {
        setMessages((prevMessages) => [
            ...prevMessages,
            { type: "bot", text: response }
        ]);
        setBotResponse("");
    };

    //TODO: Change bot response simulation to backend API
    const simulateBotResponse = (userMessage: string) => {
      setIsBotResponseGenerating(true);
      setTimeout(() => {
        const botReply = `Bot response to: ${userMessage}`;
        handleBotResponse(botReply);
        setIsBotResponseGenerating(false);
      }, 1000);
    };

    return (
        <div className={classes.mainChat}>
            <ChatList messages={messages} />
            <Spacer y={4} />
            <SearchBar
                userInput={userInput}
                setUserInput={setUserInput}
                handleUserInput={handleUserInput}
                simulateBotResponse={simulateBotResponse}
                isBotResponseGenerating={isBotResponseGenerating}
            />
        </div>
    )
}
