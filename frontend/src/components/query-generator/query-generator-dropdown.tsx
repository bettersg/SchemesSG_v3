import { Button, Dropdown, DropdownItem, DropdownMenu, DropdownTrigger } from "@nextui-org/react";

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
          className={`w-full sm:w-auto overflow-hidden self-start justify-start max-w-[160px] ${className}`}
          variant="light"
        >
          <div className="flex flex-col text-left">
            <span className="text-gray-500 text-xs">{label}</span>
            <span
              className={`text-sm font-medium truncate-first-word`}
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
      >
        {tags.map((tag) => (
          <DropdownItem key={tag}>{tag}</DropdownItem>
        ))}
      </DropdownMenu>
    </Dropdown>
  );
}

export default QueryGeneratorDropdown;