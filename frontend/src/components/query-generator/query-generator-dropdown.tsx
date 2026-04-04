<<<<<<< HEAD
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
        classNames={{
          base: 'max-h-[300px] overflow-y-auto'
        }}
      >
        {tags.map((tag) => (
          <DropdownItem key={tag}>{tag}</DropdownItem>
        ))}
      </DropdownMenu>
    </Dropdown>
  );
}

export default QueryGeneratorDropdown;
=======
import { Button, Dropdown, Label } from "@heroui/react";

interface QueryGeneratorDropdownProps {
  label: string;
  value: string;
  tags: string[];
  changeHandler: (keys: Iterable<unknown>) => void;
  className?: string;
}

function QueryGeneratorDropdown({ label, value, tags, changeHandler, className }: QueryGeneratorDropdownProps) {
  return (
    <Dropdown>
      <Dropdown.Trigger>
        <Button
          className={`w-full sm:w-auto overflow-hidden self-start justify-start max-w-[160px] ${className ?? ""}`}
          variant="light"
        >
          <div className="flex flex-col text-left">
            <span className="text-gray-500 text-xs">{label}</span>
            <span className="text-sm font-medium truncate-first-word" style={{ maxWidth: "150px" }}>
              {value}
            </span>
          </div>
        </Button>
      </Dropdown.Trigger>
      <Dropdown.Popover>
        <Dropdown.Menu
          aria-label={label}
          selectionMode="single"
          onSelectionChange={changeHandler}
          className="max-h-[300px] overflow-y-auto"
        >
          {tags.map((tag) => (
            <Dropdown.Item key={tag} id={tag} textValue={tag}>
              <Label>{tag}</Label>
            </Dropdown.Item>
          ))}
        </Dropdown.Menu>
      </Dropdown.Popover>
    </Dropdown>
  );
}

export default QueryGeneratorDropdown;
>>>>>>> 5bcdda1 (New design initial draft)
