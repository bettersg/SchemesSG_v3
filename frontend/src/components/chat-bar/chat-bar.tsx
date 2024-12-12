import { Button, Spinner, Textarea } from "@nextui-org/react";
import { SearchIcon } from '../../assets/icons/search-icon';
import classes from './chat-bar.module.css';

interface ChatBarProps {
    userInput: string;
    setUserInput: React.Dispatch<React.SetStateAction<string>>;
    handleUserInput: (message: string) => void;
    isBotResponseGenerating: boolean;
}

export default function ChatBar({ userInput, setUserInput, handleUserInput, isBotResponseGenerating }: ChatBarProps) {

    const handleSend = () => {
        if (userInput.trim()) {
          handleUserInput(userInput);
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
                        handleSend();
                    }
                }}
                className={classes.chatBar}
                type="text"
                size="md"
                radius="lg"
                color="primary"
                labelPlacement="outside"
                placeholder="Please type your question"
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
