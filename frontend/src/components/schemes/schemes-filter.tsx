import { Button, Select, SelectItem } from "@heroui/react";
import { SearchResScheme } from "./schemes-list";
import { Dispatch, SetStateAction, useMemo, useState } from "react";
import { FilterObjType } from "@/app/interfaces/filter";
import { FilterIcon } from "@/assets/icons/filter-icon";
import clsx from "clsx";
import { parseArrayString } from "@/app/utils/helper";

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
  const allLocations: string[] = useMemo(() => {
    const locationSet = new Set<string>();
    console.log(schemes);
    schemes.forEach((scheme) => {
      if (scheme.planningArea) {
        const planningAreaSet = new Set(parseArrayString(scheme.planningArea));
        planningAreaSet.forEach((planningArea) => {
          locationSet.add(planningArea);
        });
      }
    });
    // Position 'No Location' as the first option in location dropdown
    if (locationSet.has('No Location')) {
      locationSet.delete('No Location')
      return ['No Location', ...Array.from(locationSet).sort()]
    }
    return Array.from(locationSet).sort();
  }, [schemes]);

  const allAgencies = useMemo(
    () => Array.from(new Set(schemes.map((scheme) => scheme.agency))).sort(),
    [schemes]
  );

  // Filter agencies based on selected locations
  const filteredAgencies = useMemo(() => {
    if (selectedLocations.size === 0) {
      return allAgencies;
    }
    const agenciesSet = new Set<string>();
    schemes.forEach((scheme) => {
      // Skip agencies that have no planningArea
      if (!scheme.planningArea) {
        return;
      }
      // Keep agencies whose schemes have a planningArea in selectedLocations
      else if (
        selectedLocations.intersection(
          new Set(parseArrayString(scheme.planningArea))
        ).size > 0 &&
        scheme.agency
      ) {
        agenciesSet.add(scheme.agency);
      }
    });
    return Array.from(agenciesSet).sort();
  }, [selectedLocations, allAgencies, schemes]);

  // Filter locations based on selected agencies
  const filteredLocations: string[] = useMemo(() => {
    if (selectedAgencies.size === 0) {
      return allLocations;
    }
    // Keep locations whose schemes have an agency in selectedAgencies
    const locationsSet = new Set<string>();
    schemes.forEach((scheme) => {
      if (selectedAgencies.has(scheme.agency) && scheme.planningArea) {
        const planningAreaSet = new Set(parseArrayString(scheme.planningArea));
        planningAreaSet.forEach((planningArea) => {
          locationsSet.add(planningArea);
        });
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
          "absolute top-14 z-50",
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
            popoverContent: "w-max max-w-[300px] absolute right-0",
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
