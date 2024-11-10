'use client';

import { useState } from "react";
import ChatList from "@/components/chat-list/chat-list";
import SearchBar from "@/components/search-bar/search-bar";
import { Spacer } from "@nextui-org/react";

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

    return (
        <>
            <ChatList messages={messages} />
            <Spacer y={4} />
            <SearchBar
                userInput={userInput}
                setUserInput={setUserInput}
                handleUserInput={handleUserInput}
            />
        </>
    )
}
