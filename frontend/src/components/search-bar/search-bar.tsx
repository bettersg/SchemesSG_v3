import { Button, Textarea } from "@nextui-org/react";
import { SearchIcon } from './search-icon';
import classes from './search-bar.module.css';

export default function SearchBar() {

    return (
        <>
            <Textarea
                type="text"
                size="md"
                radius="lg"
                color="primary"
                label="How can we help?"
                labelPlacement="outside"
                placeholder="I am a dialysis patient in need of financial assistance and food support after being retrenched due to Covid-19."
                endContent={
                    <Button className={classes.searchButton} isIconOnly size="sm" radius="full" >
                        <SearchIcon />
                    </Button>
                }
                />
        </>
    )
}
