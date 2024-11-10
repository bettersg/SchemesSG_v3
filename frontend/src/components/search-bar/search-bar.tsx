import { Button, Textarea } from "@nextui-org/react";
import { SearchIcon } from './search-icon';
import classes from './search-bar.module.css';

interface SearchBarProps {
    userInput: string;
    setUserInput: React.Dispatch<React.SetStateAction<string>>;
    handleUserInput: (message: string) => void;
}

export default function SearchBar({ userInput, setUserInput, handleUserInput }: SearchBarProps) {

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
                className={classes.searchBar}
                type="text"
                size="md"
                radius="lg"
                color="primary"
                label="How can we help?"
                labelPlacement="outside"
                placeholder="I am a dialysis patient in need of financial assistance and food support after being retrenched due to Covid-19."
                endContent={
                    <Button className={classes.searchButton} isIconOnly size="sm" radius="full" onClick={handleSend}>
                        <SearchIcon />
                    </Button>
                }
            />
        </>
    )
}
