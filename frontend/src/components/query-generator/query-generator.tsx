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
  const [selectedForWhoState, setSelectedForWhoState] = useState("Add Who");
  const [selectedSupportProvidedState, setSelectedSupportProvidedState] =
    useState("Add Support");
  const [selectedOrganisationState, setSelectedOrganisationState] =
    useState("Add Organisation");

  const renderButton = (label: string, value: string) => {
    return (
      <div className="flex flex-col text-left">
        <span className="text-gray-500 text-xs">{label}</span>
        <span
          className={`text-sm font-medium truncate-first-word`}
          style={{ maxWidth: "150px" }}
        >
          {value}
        </span>
      </div>
    );
  };

  const handleSupportProvidedChange = (keys: Iterable<unknown>) => {
    const selected = Array.from(keys) as string[];
    const newSelected = selected.length > 0 ? selected[0] : "Add Support";
    setSelectedSupportProvided(newSelected);
    setSelectedSupportProvidedState(newSelected);
    onSendQuery();
  };

  const handleForWhoChange = (keys: Iterable<unknown>) => {
    const selected = Array.from(keys) as string[];
    const newSelected = selected.length > 0 ? selected[0] : "Add Who";
    setSelectedForWho(newSelected);
    setSelectedForWhoState(newSelected);
    onSendQuery();
  };

  const handleOrganisationChange = (keys: Iterable<unknown>) => {
    const selected = Array.from(keys) as string[];
    const newSelected = selected.length > 0 ? selected[0] : "Add Organisation";
    setSelectedOrganisation(newSelected);
    setSelectedOrganisationState(newSelected);
    onSendQuery();
  };

  return (
    <div>
      {/* Instructional Text */}
      <p className="text-sm text-gray-500 mb-2">
        Click on the options below to generate a query or write your own.
      </p>

      {/* Main Query Input */}
      <div className="border-[1px] w-full md:w-[800px] py-4 rounded-full shadow-sm hover:shadow-md transition cursor-pointer flex justify-between items-center px-2">
        {/* For Who Dropdown */}
        <Dropdown>
          <DropdownTrigger>
            <Button className="max-w-[160px] overflow-hidden" variant="light">
              {renderButton("For Who", selectedForWhoState)}
            </Button>
          </DropdownTrigger>
          <DropdownMenu
            aria-label="For Who"
            closeOnSelect={true}
            selectionMode="single"
            onSelectionChange={handleForWhoChange}
          >
            {forWhoTags.map((tag) => (
              <DropdownItem key={tag}>{tag}</DropdownItem>
            ))}
          </DropdownMenu>
        </Dropdown>

        {/* Support Provided Dropdown */}
        <Dropdown>
          <DropdownTrigger>
            <Button className="max-w-[200px] overflow-hidden" variant="light">
              {renderButton("Support Provided", selectedSupportProvidedState)}
            </Button>
          </DropdownTrigger>
          <DropdownMenu
            aria-label="Support Provided"
            closeOnSelect={true}
            selectionMode="single"
            onSelectionChange={handleSupportProvidedChange}
          >
            {supportProvidedTags.map((tag) => (
              <DropdownItem key={tag}>{tag}</DropdownItem>
            ))}
          </DropdownMenu>
        </Dropdown>

        {/* Organisation Dropdown */}
        <Dropdown>
          <DropdownTrigger>
            <Button className="max-w-[160px] overflow-hidden" variant="light">
              {renderButton("Organisation", selectedOrganisationState)}
            </Button>
          </DropdownTrigger>
          <DropdownMenu
            aria-label="Organisation"
            closeOnSelect={true}
            selectionMode="single"
            onSelectionChange={handleOrganisationChange}
          >
            {organisationTags.map((tag) => (
              <DropdownItem key={tag}>{tag}</DropdownItem>
            ))}
          </DropdownMenu>
        </Dropdown>
      </div>
    </div>
  );
};

export default QueryGenerator;
