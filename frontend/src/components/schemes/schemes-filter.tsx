import { Button, Select, SelectItem } from "@nextui-org/react";
import { SearchResScheme } from "./schemes-list";
import { Dispatch, SetStateAction } from "react";
import { FilterObjType } from "@/app/interfaces/filter";

interface SchemesFilterProps {
  schemes: SearchResScheme[];
  setFilterObj: Dispatch<SetStateAction<FilterObjType>>;
  selectedLocations: Set<string>;
  setSelectedLocations: Dispatch<SetStateAction<Set<string>>>;
  selectedAgencies: Set<string>;
  setSelectedAgencies: Dispatch<SetStateAction<Set<string>>>;
  resetFilters: () => void;
}

function SchemesFilter({schemes, setFilterObj, selectedLocations, setSelectedLocations, selectedAgencies, setSelectedAgencies, resetFilters}: SchemesFilterProps) {
  const locations = Array.from(
    new Set(
      schemes
        .filter((scheme) => scheme.planningArea)
        .map((scheme) => scheme.planningArea)
    )
  );
  const agencies = Array.from(new Set(schemes.map((scheme) => scheme.agency)));
  // const audiences = Array.from(
  //   new Set(...schemes.map((scheme) => scheme.targetAudience.split(",")))
  // );
  // const schemeTypes = Array.from(
  //   new Set(...schemes.map((scheme) => scheme.schemeType.split(",")))
  // );
  // const benefits = Array.from(
  //   new Set(...schemes.map((scheme) => scheme.benefits.split(",")))
  // );

  // console.log({ locations, agencies, audiences, schemeTypes, benefits });

  const handleFilter = () => {
    console.log(selectedLocations, selectedAgencies);
    setFilterObj({
      planningArea: selectedLocations,
      agency: selectedAgencies
    })
  };
  const handleClear = resetFilters;

  return (
      <div className="flex gap-2 flex-wrap items-center">
        <Select
          label="Locations"
          placeholder="All"
          selectionMode="multiple"
          renderValue={(items) => `${items.length} selected`}
          className="w-min min-w-[150px]"
          selectedKeys={selectedLocations}
          onSelectionChange={(keys) => setSelectedLocations(new Set(Array.from(keys) as string[]))}
        >
          {locations.map((location) => (
            <SelectItem key={location}>{location}</SelectItem>
          ))}
        </Select>
        <Select
          label="Agencies"
          placeholder="All"
          selectionMode="multiple"
          renderValue={(items) => `${items.length} selected`}
          className="w-min min-w-[200px]"
          selectedKeys={selectedAgencies}
          onSelectionChange={(keys) => setSelectedAgencies(new Set(Array.from(keys) as string[]))}
        >
          {agencies.map((agency) => (
            <SelectItem key={agency}>{agency}</SelectItem>
          ))}
        </Select>
        {/* <Select
          label="For Who"
          placeholder="All"
          selectionMode="multiple"
          renderValue={(items) => `${items.length} selected`}
          className="w-min min-w-[150px]"
          selectedKeys={selectedAudiences}
          onSelectionChange={setSelectedAudiences}
        >
          {audiences.map((audience) => (
            <SelectItem key={audience}>{audience}</SelectItem>
          ))}
        </Select>
        <Select
          label="Scheme Type"
          placeholder="All"
          selectionMode="multiple"
          renderValue={(items) => `${items.length} selected`}
          className="w-min min-w-[150px]"
          selectedKeys={selectedSchemeTypes}
          onSelectionChange={setSelectedSchemeTypes}
        >
          {schemeTypes.map((schemeType) => (
            <SelectItem key={schemeType}>{schemeType}</SelectItem>
          ))}
        </Select>
        <Select
          label="Assistance"
          placeholder="All"
          selectionMode="multiple"
          renderValue={(items) => `${items.length} selected`}
          className="w-min min-w-[150px]"
          selectedKeys={selectedBenefits}
          onSelectionChange={setSelectedBenefits}
        >
          {benefits.map((benefit) => (
            <SelectItem key={benefit}>{benefit}</SelectItem>
          ))}
        </Select> */}
        <div className="flex gap-2">
          <Button color="primary" onPress={handleFilter}>
            Filter
          </Button>
          <Button isDisabled={selectedLocations.size == 0 && selectedAgencies.size == 0} color="danger" variant="light" onPress={handleClear}>
            Clear
          </Button>
        </div>
      </div>
  );
}

export default SchemesFilter;
