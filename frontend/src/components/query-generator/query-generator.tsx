import React, { useState } from "react";
import QueryGeneratorDropdown from "./query-generator-dropdown";

// Define the props interface
interface QueryGeneratorProps {
  // setSessionId: React.Dispatch<React.SetStateAction<string>>;
  setSelectedSupportProvided: React.Dispatch<
    React.SetStateAction<string | null>
  >;
  setSelectedForWho: React.Dispatch<React.SetStateAction<string | null>>;
  setSelectedSchemeType: React.Dispatch<React.SetStateAction<string | null>>;
  // setSelectedOrganisation: React.Dispatch<React.SetStateAction<string | null>>;
  onSendQuery: () => void;
}

const forWhoTags = [
  "Low-Income Individual or Family",
  "Parent or Family Member",
  "Elderly (Senior)",
  "Person with Disabilities or Special Needs",
  "Caregiver",
  "Child or Youth",
  "Ex-Offender or Incarcerated Individual",
  "Migrant or Foreign Worker",
  "Woman in Need of Support",
  "Facing Mental Health Challenges",
  "Homeless or in Need of Shelter",
  "Dealing with Addictions or Recovery",
  "Facing End-of-Life or Terminal Illness",
  "In Need of Legal Aid",
  "Experiencing Abuse or Violence",
];

const supportProvidedTags = [
  "Financial Assistance",
  "Food Support",
  "Housing Assistance",
  "Healthcare Services",
  "Mental Health Support",
  "Education Opportunities",
  "Employment Support",
  "Caregiver Assistance",
  "Transport Mobility Support",
  "Legal Aid Services",
  "Addiction Recovery Services",
  "Parenting Support",
  "Disability Support",
  "Palliative Care Services",
  "Social Work Services",
];

const schemeTypeTags = [
  "Financial Assistance Programs",
  "Food Support",
  "Housing Assistance",
  "Shelter Services",
  "Healthcare Services",
  "Mental Health Support",
  "Education Programs",
  "Employment Assistance",
  "Caregiver Support",
  "Transport Services",
  "Legal Aid Services",
  "Addiction Recovery Services",
  "Family Support Services",
  "Disability Support Services",
  "Palliative Care Services",
  "Social Work & Casework"
];


// const organisationTags = [
//   "Housing and Development Board",
//   "Singapore Indian Development Association",
//   "SG Enable",
//   "Ministry of Health",
//   "Lakeside Family Services",
//   "Montfort Care Family Service",
//   "365 Cancer Prevention Society",
// ];

const QueryGenerator: React.FC<QueryGeneratorProps> = ({
  // setSessionId,
  setSelectedSupportProvided,
  setSelectedForWho,
  // setSelectedOrganisation,
  setSelectedSchemeType,
  onSendQuery,
}) => {
  const [selectedForWhoState, setSelectedForWhoState] = useState("Add Who");
  const [selectedSupportProvidedState, setSelectedSupportProvidedState] =
    useState("Add Support");
  // const [selectedOrganisationState, setSelectedOrganisationState] =
  //   useState("Add Organisation");
  const [selectedSchemeTypeState, setSelectedSchemeTypeState] =
    useState("Add Scheme Type");

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

  // const handleOrganisationChange = (keys: Iterable<unknown>) => {
  //   const selected = Array.from(keys) as string[];
  //   const newSelected = selected.length > 0 ? selected[0] : "Add Organisation";
  //   setSelectedOrganisation(newSelected);
  //   setSelectedOrganisationState(newSelected);
  //   onSendQuery();
  // };

  const handleSchemeTypeChange = (keys: Iterable<unknown>) => {
    const selected = Array.from(keys) as string[];
    const newSelected = selected.length > 0 ? selected[0] : "Add Scheme Type";
    setSelectedSchemeType(newSelected);
    setSelectedSchemeTypeState(newSelected);
    onSendQuery();
  };

  return (
    <div>
      {/* Instructional Text */}
      <p className="text-sm text-gray-500 mb-4 text-center">
        Click on the options below to generate a query or write your own.
      </p>

      {/* Main Query Input */}
      <div className="border-[1px] w-full sm:w-[600px] md:w-[800px] py-4 rounded-lg md:rounded-full shadow-sm hover:shadow-md transition cursor-pointer bg-slate-50">
        <div className="flex flex-col sm:flex-row justify-between items-center px-4 sm:px-6 gap-4 sm:gap-2">
          <QueryGeneratorDropdown 
            label="For Who"
            value={selectedForWhoState}
            tags={forWhoTags}
            changeHandler={handleForWhoChange}
          />
          <QueryGeneratorDropdown 
            label="Scheme Type"
            value={selectedSchemeTypeState}
            tags={schemeTypeTags}
            changeHandler={handleSchemeTypeChange}
          />
          <QueryGeneratorDropdown 
            label="Support Provided"
            value={selectedSupportProvidedState}
            tags={supportProvidedTags}
            changeHandler={handleSupportProvidedChange}
            className="max-w-[220px]"
          />
          {/* <QueryGeneratorDropdown 
            label="Organisation"
            value={selectedOrganisationState}
            tags={organisationTags}
            changeHandler={handleOrganisationChange}
          /> */}
        </div>
      </div>
    </div>
  );
};

export default QueryGenerator;
