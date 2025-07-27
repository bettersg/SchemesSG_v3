import {
  Button,
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@heroui/react";
import { InfoIcon } from "../../assets/icons/info-icon";

interface QuerySuggestionsProps {
  setUserInput: (input: string) => void;
}

const QuerySuggestions = ({ setUserInput }: QuerySuggestionsProps) => {
  const suggestions = [
    "Can you summarise the eligibility requirements and benefits for <insert scheme name here>?",
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
          className="text-schemes-darkgray hover:text-schemes-darkblue"
        >
          <InfoIcon size={16} />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[320px] rounded-xl shadow-md">
        <div className="p-4">
          <h3 className="text-lg mb-3 text-schemes-darkblue">Suggested Questions</h3>
          <ul className="flex flex-col gap-1.5">
            {suggestions.map((query, index) => (
              <li
                key={index}
                onClick={() => handleSuggestionClick(query)}
                className="text-schemes-darkgray px-3 py-2 rounded-md cursor-pointer hover:bg-schemes-lightgray hover:text-schemes-blue"
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
