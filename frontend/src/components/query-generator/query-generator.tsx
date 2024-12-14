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

const QueryGenerator = () => {
  const [selectedTag, setSelectedTag] = useState(new Set(["Scheme Type"]));
  const [selectedForWho, setSelectedForWho] = useState(new Set(["For Who"]));
  const [selectedSupportProvided, setSelectedSupportProvided] = useState(
    new Set(["Support Provided"])
  );
  const [selectedOrganisation, setSelectedOrganisation] = useState(
    new Set(["Organisation"])
  );
  const selectedOrganisationText = Array.from(selectedOrganisation)[0];
  const [firstWord, ...restWords] = selectedOrganisationText.split(" ");
  const truncatedText = restWords.join(" ");

  const renderButton = (selectedText: string) => {
    const [firstWord, ...restWords] = selectedText.split(" ");
    const truncatedText = restWords.join(" ");

    return (
      <span className={`${styles.truncate} inline-block`}>
        {firstWord} {truncatedText}
      </span>
    );
  };

  return (
    <div className="border-[1px] w-full md:w-auto py-4 rounded-full shadow-sm hover:shadow-md transition cursor-pointer flex justify-between items-center px-4">
      <Dropdown>
        <DropdownTrigger>
          <Button className="max-w-[150px] overflow-hidden" variant="light">
            {renderButton(Array.from(selectedTag)[0])}
          </Button>
        </DropdownTrigger>
        <DropdownMenu
          aria-label="Tags"
          selectionMode="single"
          onSelectionChange={(keys) =>
            setSelectedTag(new Set([Array.from(keys)[0] as string]))
          }
        >
          {tags.map((tag) => (
            <DropdownItem key={tag}>{tag}</DropdownItem>
          ))}
        </DropdownMenu>
      </Dropdown>

      <Dropdown>
        <DropdownTrigger>
          <Button className="max-w-[100px] overflow-hidden" variant="light">
            {renderButton(Array.from(selectedForWho)[0])}
          </Button>
        </DropdownTrigger>
        <DropdownMenu
          aria-label="For Who"
          selectionMode="single"
          onSelectionChange={(keys) =>
            setSelectedForWho(new Set([Array.from(keys)[0] as string]))
          }
        >
          {forWhoTags.map((tag) => (
            <DropdownItem key={tag}>{tag}</DropdownItem>
          ))}
        </DropdownMenu>
      </Dropdown>

      <Dropdown>
        <DropdownTrigger>
          <Button className="max-w-[150px] overflow-hidden" variant="light">
            {renderButton(Array.from(selectedSupportProvided)[0])}
          </Button>
        </DropdownTrigger>
        <DropdownMenu
          aria-label="Support Provided"
          selectionMode="single"
          onSelectionChange={(keys) =>
            setSelectedSupportProvided(new Set([Array.from(keys)[0] as string]))
          }
        >
          {supportProvidedTags.map((tag) => (
            <DropdownItem key={tag}>{tag}</DropdownItem>
          ))}
        </DropdownMenu>
      </Dropdown>

      <Dropdown>
        <DropdownTrigger>
          <Button className="max-w-[115px] overflow-hidden" variant="light">
            {renderButton(Array.from(selectedOrganisation)[0])}
          </Button>
        </DropdownTrigger>
        <DropdownMenu
          aria-label="Organisation"
          selectionMode="single"
          onSelectionChange={(keys) =>
            setSelectedOrganisation(new Set([Array.from(keys)[0] as string]))
          }
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
