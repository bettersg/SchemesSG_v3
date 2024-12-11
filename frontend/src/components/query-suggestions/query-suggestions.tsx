import {
  Button,
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@nextui-org/react";
import { InfoIcon } from "../../assets/icons/info-icon";
import classes from "./query-suggestions.module.css";

interface QuerySuggestionsProps {
  setUserInput: (input: string) => void;
}

const QuerySuggestions = ({ setUserInput }: QuerySuggestionsProps) => {
  const suggestions = [
    "Can you summarize the eligibility requirements and benefits for <insert scheme name here>?",
    "Can you draft an email template to apply for <insert scheme name here>?",
    "What are the typical processing times and next steps after applying?",
  ];

  const handleSuggestionClick = (query: string) => {
    setUserInput(query);
  };

  return (
    <Popover placement="bottom" showArrow={false}>
      <PopoverTrigger>
        <Button
          isIconOnly
          size="sm"
          variant="light"
          className={classes.infoButton}
        >
          <InfoIcon />
        </Button>
      </PopoverTrigger>
      <PopoverContent className={classes.popoverContent}>
        <div className="p-4">
          <h3 className={classes.title}>Suggested Questions</h3>
          <ul className={classes.suggestionList}>
            {suggestions.map((query, index) => (
              <li
                key={index}
                onClick={() => handleSuggestionClick(query)}
                className={classes.suggestionItem}
              >
                {query}
              </li>
            ))}
          </ul>
        </div>
      </PopoverContent>
    </Popover>
  );
};

export default QuerySuggestions;
