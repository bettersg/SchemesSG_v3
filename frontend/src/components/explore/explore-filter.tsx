import { Button, Label, ListBox, Select } from "@heroui/react";
import { SearchResScheme } from "./schemes-list";
import { Dispatch, SetStateAction, useMemo, useState } from "react";
import { FilterObjType } from "@/types/filter";
import { FilterIcon } from "@/assets/icons/filter-icon";
import clsx from "clsx";
import { parseArrayString } from "@/lib/helper";

interface SchemesFilterProps {
  schemes: SearchResScheme[];
  setFilterObj: Dispatch<SetStateAction<FilterObjType>>;
  selectedLocations: Set<string>;
  setSelectedLocations: Dispatch<SetStateAction<Set<string>>>;
  selectedAgencies: Set<string>;
  setSelectedAgencies: Dispatch<SetStateAction<Set<string>>>;
  resetFilters: () => void;
}

export default function ExploreFilter({
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
    schemes.forEach((scheme) => {
      if (scheme.planningArea) {
        new Set(parseArrayString(scheme.planningArea)).forEach((pa) => locationSet.add(pa));
      }
    });
    if (locationSet.has("No Location")) {
      locationSet.delete("No Location");
      return ["No Location", ...Array.from(locationSet).sort()];
    }
    return Array.from(locationSet).sort();
  }, [schemes]);

  const allAgencies = useMemo(
    () => Array.from(new Set(schemes.map((s) => s.agency))).sort(),
    [schemes]
  );

  const filteredAgencies = useMemo(() => {
    if (selectedLocations.size === 0) return allAgencies;
    const set = new Set<string>();
    schemes.forEach((scheme) => {
      if (!scheme.planningArea) return;
      if (
        selectedLocations.intersection(new Set(parseArrayString(scheme.planningArea))).size > 0 &&
        scheme.agency
      ) {
        set.add(scheme.agency);
      }
    });
    return Array.from(set).sort();
  }, [selectedLocations, allAgencies, schemes]);

  const filteredLocations: string[] = useMemo(() => {
    if (selectedAgencies.size === 0) return allLocations;
    const set = new Set<string>();
    schemes.forEach((scheme) => {
      if (selectedAgencies.has(scheme.agency) && scheme.planningArea) {
        new Set(parseArrayString(scheme.planningArea)).forEach((pa) => set.add(pa));
      }
    });
    return Array.from(set).sort();
  }, [selectedAgencies, allLocations, schemes]);

  const handleFilter = () => {
    setFilterObj({ planningArea: selectedLocations, agency: selectedAgencies });
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
        <FilterIcon />
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
        {/* Locations Select */}
        <Select
          className="w-full min-w-[150px]"
          placeholder="All"
          selectionMode="multiple"
          selectedKeys={selectedLocations}
          onSelectionChange={(keys) =>
            setSelectedLocations(new Set(Array.from(keys) as string[]))
          }
        >
          <Label>Locations</Label>
          <Select.Trigger className="bg-schemes-lightblue">
            <Select.Value />
            <Select.Indicator />
          </Select.Trigger>
          <Select.Popover>
            <ListBox>
              {filteredLocations.map((location) => (
                <ListBox.Item key={location} id={location} textValue={location}>
                  <Label>{location}</Label>
                </ListBox.Item>
              ))}
            </ListBox>
          </Select.Popover>
        </Select>

        {/* Agencies Select */}
        <Select
          className="w-full min-w-[150px]"
          placeholder="All"
          selectionMode="multiple"
          selectedKeys={selectedAgencies}
          onSelectionChange={(keys) =>
            setSelectedAgencies(new Set(Array.from(keys) as string[]))
          }
        >
          <Label>Agencies</Label>
          <Select.Trigger className="bg-schemes-lightblue">
            <Select.Value />
            <Select.Indicator />
          </Select.Trigger>
          <Select.Popover className="max-w-[300px]">
            <ListBox>
              {filteredAgencies.map((agency) => (
                <ListBox.Item key={agency} id={agency} textValue={agency}>
                  <Label>{agency}</Label>
                </ListBox.Item>
              ))}
            </ListBox>
          </Select.Popover>
        </Select>

        <div className="flex gap-2">
          <Button color="primary" onPress={handleFilter}>
            Filter
          </Button>
          <Button
            isDisabled={selectedLocations.size === 0 && selectedAgencies.size === 0}
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
