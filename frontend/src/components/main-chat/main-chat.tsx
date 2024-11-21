'use client';

import { useState } from "react";
import ChatList from "@/components/chat-list/chat-list";
import ChatBar from "@/components/chat-bar/chat-bar";
import { Spacer } from "@nextui-org/react";
import classes from "./main-chat.module.css"
import { Message } from "@/app/providers";

export default function MainChat({sessionID = "435cd734-a80b-11ef-84f7-0242ac120002"}) {
    const [messages, setMessages] = useState<Message[]>([
        { type: "bot", text: "Hello! How can I help you today?" }
    ]);
    const [userInput, setUserInput] = useState("");
    // const [botResponse, setBotResponse] = useState("");
    const [isBotResponseGenerating, setIsBotResponseGenerating] = useState<boolean>(false);

    const handleUserInput = async (input: string) => {
        setMessages((prevMessages) => [
            ...prevMessages,
            { type: "user", text: input }
        ]);
        setUserInput("");
        // Trigger API call for bot response
        await fetchBotResponse(input);
    };

    const handleBotResponse = (response: string) => {
        setMessages((prevMessages) => [
            ...prevMessages,
            { type: "bot", text: response }
        ]);
        // setBotResponse("");
    };

    const fetchBotResponse = async (userMessage: string) => {
      setIsBotResponseGenerating(true);
      try {
        const response = await fetch("http://localhost:5001/schemessg-v3-dev/asia-southeast1/chat_message", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: userMessage,
            sessionID: sessionID,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to fetch bot response");
        }

        const data = await response.json();
        if (data.response) {
          handleBotResponse(data.message);
        } else {
          handleBotResponse("Sorry, something went wrong. Please try again.");
        }
      } catch (error) {
        console.error("Error fetching bot response:", error);
        handleBotResponse("Sorry, something went wrong. Please try again.");
      } finally {
        setIsBotResponseGenerating(false);
      }
    };

    return (
        <div className={classes.mainChat}>
            <ChatList messages={messages} />
            <Spacer y={4} />
            <ChatBar
                userInput={userInput}
                setUserInput={setUserInput}
                handleUserInput={handleUserInput}
                isBotResponseGenerating={isBotResponseGenerating}
            />
        </div>
    )
}
