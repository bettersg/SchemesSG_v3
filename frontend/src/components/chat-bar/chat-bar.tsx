import { Button, Spinner, Textarea } from "@nextui-org/react";
import { SearchIcon } from '../../assets/icons/search-icon';
import classes from './chat-bar.module.css';

interface ChatBarProps {
    userInput: string;
    setUserInput: React.Dispatch<React.SetStateAction<string>>;
    handleUserInput: (message: string) => void;
    simulateBotResponse: (userMessage: string) => void;
    isBotResponseGenerating: boolean
}

export default function ChatBar({ userInput, setUserInput, handleUserInput, simulateBotResponse, isBotResponseGenerating }: ChatBarProps) {

    const handleSend = () => {
        if (userInput.trim()) {
          handleUserInput(userInput);
          simulateBotResponse(userInput);
        }
    };

    return (
        <>
            <Textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                className={classes.chatBar}
                type="text"
                size="md"
                radius="lg"
                color="primary"
                label="How can we help?"
                labelPlacement="outside"
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
