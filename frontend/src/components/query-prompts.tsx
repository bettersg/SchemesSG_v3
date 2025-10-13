import { useChat } from "@/app/providers";
import { Button } from "@heroui/react";

interface queryPromptsProps {
  focusSearchbar: () => void;
}

export default function QueryPrompts({ focusSearchbar }: queryPromptsProps) {
  const prompts = {
    "I am a...": "I am a ",
    "I need support for...": "I need support for ",
    "My current situation is...": "My current situation is ",
    "Preferred location": "I prefer these locations: ",
    "Family support": "I need family support ",
    "Emotional Counseling": "I need emotional counseling ",
    "Financial support": "I need financial support ",
  };

  type Prompt = keyof typeof prompts;
  const { setUserQuery } = useChat();

  const handlePromptClick = (value: string) => {
    setUserQuery((prevQuery) => prevQuery + value);
    focusSearchbar();
  };
  return (
    <div className="flex flex-wrap gap-2">
      {Object.keys(prompts).map((prompt, index) => {
        const value = prompts[prompt as Prompt];
        return (
          <Button
            key={index}
            size="sm"
            color="primary"
            variant="bordered"
            className="border-schemes-gray border-1 bg-white"
            onPress={() => handlePromptClick(value)}
          >
            {prompt}
          </Button>
        );
      })}
    </div>
  );
}
