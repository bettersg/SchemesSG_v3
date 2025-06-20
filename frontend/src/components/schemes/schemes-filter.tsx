import { Button, Select, SelectItem } from "@nextui-org/react";
import { SearchResScheme } from "./schemes-list";
import { Dispatch, SetStateAction, useMemo } from "react";
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

function SchemesFilter({ schemes, setFilterObj, selectedLocations, setSelectedLocations, selectedAgencies, setSelectedAgencies, resetFilters }: SchemesFilterProps) {
  const allLocations = useMemo(
    () =>
      Array.from(
        new Set(
          schemes
            .filter((scheme) => scheme.planningArea)
            .map((scheme) => scheme.planningArea)
        )
      ).sort(),
    [schemes]
  );

  const allAgencies = useMemo(
    () => Array.from(new Set(schemes.map((scheme) => scheme.agency))).sort(),
    [schemes]
  );
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


  // Filter agencies based on selected locations
  const filteredAgencies = useMemo(() => {
    if (selectedLocations.size === 0) {
      return allAgencies;
    }
    // Keep agencies whose schemes have a planningArea in selectedLocations
    const agenciesSet = new Set<string>();
    schemes.forEach((scheme) => {
      if (
        selectedLocations.has(scheme.planningArea) &&
        scheme.agency
      ) {
        agenciesSet.add(scheme.agency);
      }
    });
    return Array.from(agenciesSet).sort();
  }, [selectedLocations, allAgencies, schemes]);

  // Filter locations based on selected agencies
  const filteredLocations = useMemo(() => {
    if (selectedAgencies.size === 0) {
      return allLocations;
    }
    // Keep locations whose schemes have an agency in selectedAgencies
    const locationsSet = new Set<string>();
    schemes.forEach((scheme) => {
      if (
        selectedAgencies.has(scheme.agency) &&
        scheme.planningArea
      ) {
        locationsSet.add(scheme.planningArea);
      }
    });
    return Array.from(locationsSet).sort();
  }, [selectedAgencies, allLocations, schemes]);


  const handleFilter = () => {
    console.log(selectedLocations, selectedAgencies);
    setFilterObj({
      planningArea: selectedLocations,
      agency: selectedAgencies
    })
  };
  const handleClear = () => {
    setSelectedLocations(new Set());
    setSelectedAgencies(new Set());
    resetFilters();
  };

  return (
    <div className="flex gap-2 flex-wrap items-center">
      <Select
        label="Locations"
        placeholder="All"
        selectionMode="multiple"
        renderValue={(items) => `${items.length} selected`}
        className="w-min min-w-[170px]"
        classNames={{
          trigger: "bg-[#D9E8FF] border-[#CADBFF] focus:bg-[#C0D9FF]",
        }}
        selectedKeys={selectedLocations}
        onSelectionChange={(keys) =>
          setSelectedLocations(
            new Set(Array.from(keys) as string[])
          )
        }
      >
        {filteredLocations.map((location) => (
          <SelectItem key={location}>{location}</SelectItem>
        ))}
      </Select>

      <Select
        label="Agencies"
        placeholder="All"
        selectionMode="multiple"
        renderValue={(items) => `${items.length} selected`}
        className="w-min min-w-[250px]"
        classNames={{
          trigger: "bg-[#D9E8FF] border-[#CADBFF] focus:bg-[#C0D9FF]",
        }}
        selectedKeys={selectedAgencies}
        onSelectionChange={(keys) =>
          setSelectedAgencies(
            new Set(Array.from(keys) as string[])
          )
        }
      >
        {filteredAgencies.map((agency) => (
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
        <Button
            isDisabled={selectedLocations.size == 0 && selectedAgencies.size == 0}
            color="danger"
            variant="light"
            className="border-2 border-red-500 disabled:bg-gray-200 disabled:border-gray-200 disabled:text-gray-500"
            onPress={handleClear}>
          Clear
        </Button>
      </div>
    </div>
  );
}

export default SchemesFilter;
