import React, { useState } from "react";
import { BiSearch } from "react-icons/bi";
import {
  Dropdown,
  DropdownItem,
  DropdownMenu,
  DropdownTrigger,
  Button,
} from "@nextui-org/react";
import styles from "./query-generator.module.css";

// Define the props interface
interface QueryGeneratorProps {
  setSessionId: React.Dispatch<React.SetStateAction<string>>;
  setSelectedSupportProvided: React.Dispatch<
    React.SetStateAction<string | null>
  >;
  setSelectedForWho: React.Dispatch<React.SetStateAction<string | null>>;
  setSelectedOrganisation: React.Dispatch<React.SetStateAction<string | null>>;
  onSendQuery: () => void;
}

const tags = [
  "Caregiver",
  "Childcare",
  "Children",
  "COVID-19",
  "Debt",
  "Education",
  "Elderly",
  "Employment",
  "Family",
  "Family Violence",
  "Food",
  "Healthcare",
  "Homeless",
  "Housing",
  "Ex-offender",
  "Low Income",
  "Mental Health",
  "Palliative",
  "PWD",
  "Referral",
  "Special Needs",
  "Student Care",
  "Tech",
  "Transport",
  "Women",
  "Work",
  "Youth-at-Risk",
];

const forWhoTags = [
  "Elderly",
  "Low income families",
  "Caregivers",
  "Ex-offenders",
  "Migrant workers",
  "Cancer patients",
  "HIV patients",
];

const supportProvidedTags = [
  "Educational programmes for caregivers",
  "Emotional care",
  "Financial assistance",
  "Food",
  "Counselling",
  "Financial assistance for dialysis",
  "Transport subsidy",
  "Financial assistance for assistive technology",
];

const organisationTags = [
  "Housing and Development Board",
  "Singapore Indian Development Association",
  "SG Enable",
  "Ministry of Health",
  "Lakeside Family Services",
  "Montfort Care Family Service",
  "365 Cancer Prevention Society",
];

const QueryGenerator: React.FC<QueryGeneratorProps> = ({
  setSessionId,
  setSelectedSupportProvided,
  setSelectedForWho,
  setSelectedOrganisation,
  onSendQuery,
}) => {
  const [selectedTag, setSelectedTag] = useState(new Set(["Scheme Type"]));
  const [selectedForWhoState, setSelectedForWhoState] = useState(
    new Set(["For Who"])
  );
  const [selectedSupportProvidedState, setSelectedSupportProvidedState] =
    useState(new Set(["Support Provided"]));
  const [selectedOrganisationState, setSelectedOrganisationState] = useState(
    new Set(["Organisation"])
  );

  const renderButton = (
    selectedText:
      | string
      | number
      | bigint
      | boolean
      | React.ReactElement<any, string | React.JSXElementConstructor<any>>
      | Iterable<React.ReactNode>
      | Promise<React.AwaitedReactNode>
      | null
      | undefined
  ) => {
    return (
      <span className={`${styles.truncate} inline-block font-bold`}>
        {selectedText}
      </span>
    );
  };

  const handleSupportProvidedChange = (
    keys: Iterable<unknown> | ArrayLike<unknown>
  ) => {
    const selected = Array.from(keys) as string[];
    const newSelected = selected.length > 0 ? selected[0] : "Support Provided"; // Default value
    console.log("Selected Support Provided:", newSelected);
    setSelectedSupportProvided(newSelected);
    setSelectedSupportProvidedState(new Set([newSelected]));
    onSendQuery();
  };

  const handleForWhoChange = (keys: Iterable<unknown> | ArrayLike<unknown>) => {
    const selected = Array.from(keys) as string[];
    const newSelected = selected.length > 0 ? selected[0] : "For Who"; // Default value
    setSelectedForWho(newSelected);
    setSelectedForWhoState(new Set([newSelected]));
    onSendQuery();
  };

  const handleOrganisationChange = (
    keys: Iterable<unknown> | ArrayLike<unknown>
  ) => {
    const selected = Array.from(keys) as string[];
    const newSelected = selected.length > 0 ? selected[0] : "Organisation"; // Default value
    setSelectedOrganisation(newSelected);
    setSelectedOrganisationState(new Set([newSelected]));
    onSendQuery();
  };

  return (
    <div className="border-[1px] w-full md:w-[800px] py-4 rounded-full shadow-sm hover:shadow-md transition cursor-pointer flex justify-between items-center px-4">
      <Dropdown>
        <DropdownTrigger>
          <Button className="max-w-[150px] overflow-hidden" variant="light">
            {renderButton(Array.from(selectedTag)[0])}
          </Button>
        </DropdownTrigger>
        <DropdownMenu
          aria-label="Tags"
          closeOnSelect={false}
          selectionMode="multiple"
          onSelectionChange={handleSupportProvidedChange}
        >
          {tags.map((tag) => (
            <DropdownItem key={tag}>{tag}</DropdownItem>
          ))}
        </DropdownMenu>
      </Dropdown>

      <Dropdown>
        <DropdownTrigger>
          <Button className="max-w-[100px] overflow-hidden" variant="light">
            {renderButton(Array.from(selectedForWhoState)[0])}
          </Button>
        </DropdownTrigger>
        <DropdownMenu
          aria-label="For Who"
          closeOnSelect={false}
          selectionMode="multiple"
          onSelectionChange={handleForWhoChange}
        >
          {forWhoTags.map((tag) => (
            <DropdownItem key={tag}>{tag}</DropdownItem>
          ))}
        </DropdownMenu>
      </Dropdown>

      <Dropdown>
        <DropdownTrigger>
          <Button className="max-w-[180px] overflow-hidden" variant="light">
            {renderButton(Array.from(selectedSupportProvidedState)[0])}
          </Button>
        </DropdownTrigger>
        <DropdownMenu
          aria-label="Support Provided"
          closeOnSelect={false}
          selectionMode="multiple"
          onSelectionChange={handleSupportProvidedChange}
        >
          {supportProvidedTags.map((tag) => (
            <DropdownItem key={tag}>{tag}</DropdownItem>
          ))}
        </DropdownMenu>
      </Dropdown>

      <Dropdown>
        <DropdownTrigger>
          <Button className="max-w-[130px] overflow-hidden" variant="light">
            {renderButton(Array.from(selectedOrganisationState)[0])}
          </Button>
        </DropdownTrigger>
        <DropdownMenu
          aria-label="Organisation"
          closeOnSelect={false}
          selectionMode="multiple"
          onSelectionChange={handleOrganisationChange}
        >
          {organisationTags.map((tag) => (
            <DropdownItem key={tag}>{tag}</DropdownItem>
          ))}
        </DropdownMenu>
      </Dropdown>

      <div className="p-3 bg-gradient-to-r from-blue-500 to-blue-700 rounded-full text-white">
        <BiSearch size={20} />
      </div>
    </div>
  );
};

export default QueryGenerator;
