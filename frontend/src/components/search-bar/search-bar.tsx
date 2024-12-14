'use client';

import { Button, Spinner, Textarea } from "@nextui-org/react";
import { SearchIcon } from '../../assets/icons/search-icon';
import classes from './search-bar.module.css';
import { useState } from "react";
import { useChat } from "@/app/providers";
import { Scheme } from "../schemes/schemes-list";

interface SearchBarProps {
    setSessionId: (val: string) => void;
}

const mapToScheme = (rawData: any): Scheme => {
    return {
        schemeType: rawData["Scheme Type"] || "",
        schemeName: rawData["Scheme"] || "",
        targetAudience: rawData["Who's it for"] || "",
        agency: rawData["Agency"] || "",
        description: rawData["Description"] || "",
        scrapedText: rawData["scraped_text"] || "",
        benefits: rawData["What it gives"] || "",
        link: rawData["Link"] || "",
        image: rawData["Image"] || "",
        searchBooster: rawData["search_booster(WL)"] || "",
        schemeId: rawData["scheme_id"] || "",
        query: rawData["query"] || "",
        similarity: rawData["Similarity"] || 0,
        quintile: rawData["Quintile"] || 0
    };
};

export default function SearchBar({ setSessionId }: SearchBarProps) {
    const { setMessages, setUserQuery, setSchemes } = useChat();
    const [userInput, setUserInput] = useState("");
    const [isBotResponseGenerating, setIsBotResponseGenerating] = useState<boolean>(false);

    const handleUserInput = (input: string) => {
        setMessages([
            { type: "bot", text: "You can see the search results on the right. Please ask me any further questions about the schemes." }
        ]);
        setUserQuery(input);
        setUserInput("");
    };

    const getSchemes = async () => {
        const url = "http://localhost:5001/schemessg-v3-dev/asia-southeast1/schemes_search";

        const requestBody = {
            query: userInput,
            top_k: 20,
            similarity_threshold: 0
        };

        try {
            setIsBotResponseGenerating(true);
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const res = await response.json();
            const sessionId: string = res["sessionID"];
            setIsBotResponseGenerating(false);
            const schemesRes: Scheme[] = res.data.map(mapToScheme);
            return { schemesRes, sessionId };
        } catch (error) {
            console.error("Error making POST request:", error);
            setIsBotResponseGenerating(false);
            return { schemesRes: [], sessionId: "" };
        }

    };

    const handleSend = async () => {
        if (userInput.trim()) {
            const { schemesRes, sessionId } = await getSchemes();
            if (schemesRes.length > 0 && sessionId !== "") {
                schemesRes && setSchemes(schemesRes);
                setSessionId(sessionId);
                handleUserInput(userInput);
            }
        }
    };

    return (
        <>
            <Textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={async (e) => {
                    if (e.key === "Enter" && !isBotResponseGenerating) {
                        e.preventDefault();
                        await handleSend();
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
                    isBotResponseGenerating
                    ? <Spinner className={classes.endContent} size="sm" />
                    : <Button className={classes.endContent} isIconOnly size="sm" radius="full" onClick={async () => await handleSend()}>
                        <SearchIcon />
                    </Button>
                }
            />
        </>
    )
}
