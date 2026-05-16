import { Button, Dropdown, DropdownItem, DropdownMenu, DropdownTrigger } from "@heroui/react";

interface QueryGeneratorDropdownProps {
  label: string;
  value: string;
  tags: string[];
  changeHandler: (keys: Iterable<unknown>) => void;
  className?: string;
}

function QueryGeneratorDropdown({label, value, tags, changeHandler, className}: QueryGeneratorDropdownProps) {
  return (
    <Dropdown>
      <DropdownTrigger>
        <Button
          className={`w-full sm:w-auto overflow-hidden self-start justify-start max-w-[160px] border border-(--schemes-border) bg-white text-(--schemes-ink) hover:bg-(--schemes-blue-50) ${className}`}
          variant="outline"
        >
          <div className="flex flex-col text-left">
            <span className="text-(--schemes-muted) text-xs">{label}</span>
            <span
              className="text-sm font-semibold text-(--schemes-blue-900) truncate-first-word"
              style={{ maxWidth: "150px" }}
            >
              {value}
            </span>
          </div>
        </Button>
      </DropdownTrigger>
      <DropdownMenu
        aria-label={label}
        closeOnSelect={true}
        selectionMode="single"
        onSelectionChange={changeHandler}
        classNames={{
          base: "max-h-[300px] overflow-y-auto bg-white text-(--schemes-ink)"
        }}
      >
        {tags.map((tag) => (
          <DropdownItem key={tag} className="text-(--schemes-ink)">
            {tag}
          </DropdownItem>
        ))}
      </DropdownMenu>
    </Dropdown>
  );
}

export default QueryGeneratorDropdown;
