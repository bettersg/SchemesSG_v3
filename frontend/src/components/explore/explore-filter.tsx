import { Button, Label, ListBox, Popover, Select } from "@heroui/react";
import { Scheme } from "@/types/types";
import type { Key } from "react";
import { Dispatch, SetStateAction, useMemo } from "react";
import { FilterObjType } from "@/types/types";
import { Funnel } from "lucide-react";
import { parseArrayString } from "@/lib/utils";

interface SchemesFilterProps {
  schemes: Scheme[];
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
  const allLocations: string[] = useMemo(() => {
    const locationSet = new Set<string>();
    schemes.forEach((scheme) => {
      if (scheme.planningArea) {
        new Set(parseArrayString(scheme.planningArea)).forEach((pa) =>
          locationSet.add(pa),
        );
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
    [schemes],
  );

  const filteredAgencies = useMemo(() => {
    if (selectedLocations.size === 0) return allAgencies;
    const set = new Set<string>();
    schemes.forEach((scheme) => {
      if (!scheme.planningArea) return;
      if (
        selectedLocations.intersection(
          new Set(parseArrayString(scheme.planningArea)),
        ).size > 0 &&
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
        new Set(parseArrayString(scheme.planningArea)).forEach((pa) =>
          set.add(pa),
        );
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

  const selectionToStringSet = (keys: "all" | Iterable<Key>) => {
    if (keys === "all") {
      return new Set<string>();
    }
    return new Set(Array.from(keys).map(String));
  };

  const renderFilterControls = () => (
    <>
      {/* Locations Select */}
      <Select
        className="w-full min-w-[150px]"
        placeholder="All"
        selectionMode="multiple"
        selectedKeys={selectedLocations}
        onSelectionChange={(keys: "all" | Iterable<Key>) =>
          setSelectedLocations(selectionToStringSet(keys))
        }
      >
        <Label>Locations</Label>
        <Select.Trigger className="border border-(--schemes-blue-100) bg-gradient-to-b from-white to-(--schemes-status-info-bg) text-(--schemes-blue-900) font-semibold shadow-none">
          <Select.Value className="text-(--schemes-blue-900)" />
          <Select.Indicator className="text-(--schemes-blue-900)" />
        </Select.Trigger>
        <Select.Popover className="bg-white text-(--schemes-ink)">
          <ListBox className="text-(--schemes-ink)">
            {filteredLocations.map((location) => (
              <ListBox.Item
                key={location}
                id={location}
                textValue={location}
                className="text-(--schemes-ink) data-[focused]:bg-(--schemes-blue-50) data-[selected]:text-(--schemes-blue-900)"
              >
                <Label className="text-(--schemes-ink)">{location}</Label>
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
        onSelectionChange={(keys: "all" | Iterable<Key>) =>
          setSelectedAgencies(selectionToStringSet(keys))
        }
      >
        <Label>Agencies</Label>
        <Select.Trigger className="border border-(--schemes-blue-100) bg-gradient-to-b from-white to-(--schemes-status-info-bg) text-(--schemes-blue-900) font-semibold shadow-none">
          <Select.Value className="text-(--schemes-blue-900)" />
          <Select.Indicator className="text-(--schemes-blue-900)" />
        </Select.Trigger>
        <Select.Popover className="max-w-[300px] bg-white text-(--schemes-ink)">
          <ListBox className="text-(--schemes-ink)">
            {filteredAgencies.map((agency) => (
              <ListBox.Item
                key={agency}
                id={agency}
                textValue={agency}
                className="text-(--schemes-ink) data-[focused]:bg-(--schemes-blue-50) data-[selected]:text-(--schemes-blue-900)"
              >
                <Label className="text-(--schemes-ink)">{agency}</Label>
              </ListBox.Item>
            ))}
          </ListBox>
        </Select.Popover>
      </Select>

      <div className="flex gap-2">
        <Button
          variant="primary"
          className="bg-(--schemes-amber-400) text-(--schemes-ink) hover:bg-(--schemes-amber-100) font-semibold"
          onPress={handleFilter}
        >
          Filter
        </Button>
        <Button
          isDisabled={
            selectedLocations.size === 0 && selectedAgencies.size === 0
          }
          variant="outline"
          className="border-(--schemes-border-neutral) bg-white text-(--schemes-ink-soft) hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900) disabled:bg-gray-200 disabled:border-gray-200 disabled:text-gray-500"
          onPress={handleClear}
        >
          Clear
        </Button>
      </div>
    </>
  );

  return (
    <div className="w-full flex gap-2 flex-wrap relative items-center lg:justify-end">
      <div className="lg:hidden">
        <Popover>
          <Button
            isIconOnly
            variant="ghost"
            className="text-(--schemes-blue-900)"
            aria-label="Filter schemes"
          >
            <Funnel size={24} strokeWidth={2} />
          </Button>
          <Popover.Content
            placement="bottom start"
            className="z-50 w-[min(78vw,320px)] rounded-xl border border-(--schemes-border) bg-(--schemes-surface) p-0 shadow-sm"
          >
            <Popover.Dialog className="m-0 flex flex-col items-end gap-2 p-3 outline-none">
              {renderFilterControls()}
            </Popover.Dialog>
          </Popover.Content>
        </Popover>
      </div>
      <div className="hidden items-end gap-2 lg:flex lg:flex-row">
        {renderFilterControls()}
      </div>
    </div>
  );
}
