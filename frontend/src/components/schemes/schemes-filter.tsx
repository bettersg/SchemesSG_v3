import { Button, Label, ListBox, Popover, Select } from "@heroui/react";
import type { Key } from "react";
import { Scheme } from "@/types/types";
import { Dispatch, SetStateAction, useMemo } from "react";
import { FilterObjType } from "@/app/interfaces/filter";
import { Funnel } from "lucide-react";
import clsx from "clsx";
import { capitalize, parseArrayString } from "@/lib/utils";
import {
  productButtonPrimary,
  productButtonSecondary,
  productButtonSm,
  productButtonTertiary,
} from "@/lib/design-system/product-styles";

interface SchemesFilterProps {
  schemes: Scheme[];
  setFilterObj: Dispatch<SetStateAction<FilterObjType>>;
  selectedLocations: Set<string>;
  setSelectedLocations: Dispatch<SetStateAction<Set<string>>>;
  selectedAgencies: Set<string>;
  setSelectedAgencies: Dispatch<SetStateAction<Set<string>>>;
  resetFilters: () => void;
  mode?: "toolbar" | "compact";
  className?: string;
}

const filterLabelClass =
  "text-[11px] font-semibold leading-none text-(--schemes-muted)";

const filterSelectTrigger =
  "h-9 rounded-lg border border-(--schemes-blue-100) bg-white px-3 text-xs font-semibold text-(--schemes-blue-600) shadow-none transition-[background-color,border-color,color,box-shadow] hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900) focus-visible:border-(--schemes-blue-400) focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)";

const filterSelectValueClass =
  "text-xs font-semibold text-(--schemes-blue-600)";

const filterSelectPopover =
  "rounded-lg border border-(--schemes-border) bg-white p-1 text-(--schemes-ink) shadow-sm";

const filterListBoxClass = "text-xs text-(--schemes-ink-soft)";

const filterListBoxItemClass =
  "rounded-md px-2 py-1.5 text-xs text-(--schemes-ink-soft) data-[focused]:bg-(--schemes-blue-50) data-[selected]:font-semibold data-[selected]:text-(--schemes-blue-900)";

type SelectChangeValue = Key | Iterable<Key> | null | undefined;

function SchemesFilter({
  schemes,
  setFilterObj,
  selectedLocations,
  setSelectedLocations,
  selectedAgencies,
  setSelectedAgencies,
  resetFilters,
  mode = "toolbar",
  className,
}: SchemesFilterProps) {
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
    if (locationSet.has("No Location")) {
      locationSet.delete("No Location");
      return ["No Location", ...Array.from(locationSet).sort()];
    }
    return Array.from(locationSet).sort();
  }, [schemes]);

  const allAgencies = useMemo(
    () => Array.from(new Set(schemes.map((scheme) => scheme.agency))).sort(),
    [schemes],
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
          new Set(parseArrayString(scheme.planningArea)),
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

  const locationValue = Array.from(selectedLocations) as Key[];
  const agencyValue = Array.from(selectedAgencies) as Key[];

  const getSelectedCountLabel = (count: number) =>
    count === 0 ? "All" : `${count} selected`;
  const isCompact = mode === "compact";
  const selectValueToStringSet = (value: SelectChangeValue) => {
    if (value == null) {
      return new Set<string>();
    }
    if (
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "bigint"
    ) {
      return new Set([String(value)]);
    }
    return new Set(Array.from(value).map(String));
  };

  const filterControls = (
    <>
      <Select
        variant="secondary"
        selectionMode="multiple"
        placeholder="All"
        value={locationValue}
        onChange={(value: SelectChangeValue) =>
          setSelectedLocations(selectValueToStringSet(value))
        }
        className="w-full min-w-[150px]"
      >
        <Label className={filterLabelClass}>Locations</Label>
        <Select.Trigger className={filterSelectTrigger}>
          <Select.Value className={filterSelectValueClass}>
            {getSelectedCountLabel(selectedLocations.size)}
          </Select.Value>
          <Select.Indicator className="text-(--schemes-blue-600)" />
        </Select.Trigger>
        <Select.Popover className={`w-max ${filterSelectPopover}`}>
          <ListBox selectionMode="multiple" className={filterListBoxClass}>
            {filteredLocations.map((location) => (
              <ListBox.Item
                key={location}
                id={location}
                textValue={location}
                className={filterListBoxItemClass}
              >
                {capitalize(location)}
                <ListBox.ItemIndicator />
              </ListBox.Item>
            ))}
          </ListBox>
        </Select.Popover>
      </Select>

      <Select
        variant="secondary"
        selectionMode="multiple"
        placeholder="All"
        value={agencyValue}
        onChange={(value: SelectChangeValue) =>
          setSelectedAgencies(selectValueToStringSet(value))
        }
        className="w-full min-w-[150px]"
      >
        <Label className={filterLabelClass}>Agencies</Label>
        <Select.Trigger className={filterSelectTrigger}>
          <Select.Value className={filterSelectValueClass}>
            {getSelectedCountLabel(selectedAgencies.size)}
          </Select.Value>
          <Select.Indicator className="text-(--schemes-blue-600)" />
        </Select.Trigger>
        <Select.Popover className={`w-max max-w-[300px] ${filterSelectPopover}`}>
          <ListBox selectionMode="multiple" className={filterListBoxClass}>
            {filteredAgencies.map((agency) => (
              <ListBox.Item
                key={agency}
                id={agency}
                textValue={agency}
                className={filterListBoxItemClass}
              >
                {agency}
                <ListBox.ItemIndicator />
              </ListBox.Item>
            ))}
          </ListBox>
        </Select.Popover>
      </Select>

      <div className="flex gap-2 items-end">
        <Button
          variant="primary"
          className={`${productButtonPrimary} ${productButtonSm}`}
          onPress={handleFilter}
        >
          Filter
        </Button>
        <Button
          isDisabled={
            selectedLocations.size === 0 && selectedAgencies.size === 0
          }
          variant="outline"
          className={`${productButtonTertiary} ${productButtonSm}`}
          onPress={handleClear}
        >
          Clear
        </Button>
      </div>
    </>
  );

  if (isCompact) {
    return (
      <div className={clsx("shrink-0", className)}>
        <Popover>
          <Button
            size="sm"
            variant="outline"
            aria-label="Filter schemes"
            className={`${productButtonSecondary} ${productButtonSm} h-9 min-h-0 shrink-0`}
          >
            <Funnel className="!h-4 !w-4 shrink-0" strokeWidth={2} />
            Filter
          </Button>
          <Popover.Content
            placement="bottom end"
            className="z-50 w-[min(78vw,320px)] rounded-xl border border-(--schemes-border) bg-(--schemes-surface) p-0 shadow-sm"
          >
            <Popover.Dialog className="m-0 flex flex-col gap-2 p-3 outline-none">
              {filterControls}
            </Popover.Dialog>
          </Popover.Content>
        </Popover>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        "w-full flex gap-2 flex-wrap relative items-center justify-end border-b px-4 py-2",
        className,
      )}
    >
      <div className="flex flex-row items-end gap-2">{filterControls}</div>
    </div>
  );
}

export default SchemesFilter;
