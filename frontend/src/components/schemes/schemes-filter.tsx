import { Button, Select, SelectItem } from "@nextui-org/react";
import { SearchResScheme } from "./schemes-list";
import { Dispatch, SetStateAction, useMemo, useState } from "react";
import { FilterObjType } from "@/app/interfaces/filter";
import { FilterIcon } from "@/assets/icons/filter-icon";
import clsx from "clsx";

interface SchemesFilterProps {
  schemes: SearchResScheme[];
  setFilterObj: Dispatch<SetStateAction<FilterObjType>>;
  selectedLocations: Set<string>;
  setSelectedLocations: Dispatch<SetStateAction<Set<string>>>;
  selectedAgencies: Set<string>;
  setSelectedAgencies: Dispatch<SetStateAction<Set<string>>>;
  resetFilters: () => void;
}

function SchemesFilter({
  schemes,
  setFilterObj,
  selectedLocations,
  setSelectedLocations,
  selectedAgencies,
  setSelectedAgencies,
  resetFilters,
}: SchemesFilterProps) {
  const [showFilter, setShowFilter] = useState(false);
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

  // Filter agencies based on selected locations
  const filteredAgencies = useMemo(() => {
    if (selectedLocations.size === 0) {
      return allAgencies;
    }
    // Keep agencies whose schemes have a planningArea in selectedLocations
    const agenciesSet = new Set<string>();
    schemes.forEach((scheme) => {
      if (selectedLocations.has(scheme.planningArea) && scheme.agency) {
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
      if (selectedAgencies.has(scheme.agency) && scheme.planningArea) {
        locationsSet.add(scheme.planningArea);
      }
    });
    return Array.from(locationsSet).sort();
  }, [selectedAgencies, allLocations, schemes]);

  const handleFilter = () => {
    console.log(selectedLocations, selectedAgencies);
    setFilterObj({
      planningArea: selectedLocations,
      agency: selectedAgencies,
    });
  };
  const handleClear = () => {
    setSelectedLocations(new Set());
    setSelectedAgencies(new Set());
    resetFilters();
  };

  return (
    <div className="w-full flex gap-2 flex-wrap relative items-center xl:justify-end">
      <Button
        color="primary"
        isIconOnly
        variant="light"
        className="xl:hidden"
        onPress={() => setShowFilter(!showFilter)}
      >
        <FilterIcon size={32} />
      </Button>
      <div
        className={clsx(
          "max-xl:bg-schemes-lightgray max-xl:p-2 max-xl:rounded-lg max-xl:shadow-md",
          "absolute top-14 z-20", 
          showFilter ? "flex" : "hidden",
          "flex-col gap-2 items-end",
          "xl:static xl:flex xl:flex-row"
        )}
      >
        <Select
          label="Locations"
          placeholder="All"
          selectionMode="multiple"
          renderValue={(items) => `${items.length} selected`}
          className="w-full min-w-[150px]"
          classNames={{
            trigger: "bg-schemes-lightblue",
            popoverContent: "w-max",
          }}
          selectedKeys={selectedLocations}
          onSelectionChange={(keys) =>
            setSelectedLocations(new Set(Array.from(keys) as string[]))
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
          className="w-full min-w-[150px]"
          classNames={{
            trigger: "bg-schemes-lightblue",
            popoverContent: "w-max",
          }}
          selectedKeys={selectedAgencies}
          onSelectionChange={(keys) =>
            setSelectedAgencies(new Set(Array.from(keys) as string[]))
          }
        >
          {filteredAgencies.map((agency) => (
            <SelectItem key={agency}>{agency}</SelectItem>
          ))}
        </Select>
        <div className="flex gap-2">
          <Button color="primary" onPress={handleFilter}>
            Filter
          </Button>
          <Button
            isDisabled={
              selectedLocations.size == 0 && selectedAgencies.size == 0
            }
            color="danger"
            variant="light"
            className="border-2 border-red-500 disabled:bg-gray-200 disabled:border-gray-200 disabled:text-gray-500"
            onPress={handleClear}
          >
            Clear
          </Button>
        </div>
      </div>
    </div>
  );
}

export default SchemesFilter;
