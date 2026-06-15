import { Button, Drawer, Popover, useOverlayState } from "@heroui/react";
import { Scheme } from "@/types/types";
import { Dispatch, SetStateAction, useEffect, useMemo, useState } from "react";
import { FilterObjType } from "@/app/interfaces/filter";
import {
  Building2,
  Check,
  ChevronDown,
  type LucideIcon,
  MapPin,
  Search,
  X,
} from "lucide-react";
import clsx from "clsx";
import { capitalize, parseArrayString } from "@/lib/utils";

// True on tablet/desktop (>=768px), matching the app's `md` breakpoint. Drives
// the filter affordance: a popover on desktop, a bottom-sheet drawer on mobile
// where popover rows are too small to tap reliably.
function useIsDesktop() {
  const [isDesktop, setIsDesktop] = useState(true);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const update = () => setIsDesktop(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return isDesktop;
}

interface SchemesFilterProps {
  schemes: Scheme[];
  setFilterObj: Dispatch<SetStateAction<FilterObjType>>;
  selectedLocations: Set<string>;
  setSelectedLocations: Dispatch<SetStateAction<Set<string>>>;
  selectedAgencies: Set<string>;
  setSelectedAgencies: Dispatch<SetStateAction<Set<string>>>;
  resetFilters: () => void;
  className?: string;
}

type FilterChipProps = {
  icon: LucideIcon;
  label: string;
  unit: string; // plural noun for the active count, e.g. "areas", "agencies"
  options: string[];
  selected: Set<string>;
  onChange: (next: Set<string>) => void;
  formatOption?: (value: string) => string;
};

// Shared multi-select body: a search row over a scrollable checkbox list.
// `size` scales the rows — "sm" for the desktop popover, "lg" for the mobile
// drawer where each row must clear the 44–48px touch-target minimum.
function FilterPanel({
  label,
  options,
  selected,
  onChange,
  formatOption,
  size,
}: {
  label: string;
  options: string[];
  selected: Set<string>;
  onChange: (next: Set<string>) => void;
  formatOption: (value: string) => string;
  size: "sm" | "lg";
}) {
  const [query, setQuery] = useState("");
  const active = selected.size > 0;
  const lg = size === "lg";

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options;
    return options.filter((o) => o.toLowerCase().includes(q));
  }, [options, query]);

  const toggle = (value: string) => {
    const next = new Set(selected);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    onChange(next);
  };

  return (
    <>
      <div
        className={clsx(
          "flex shrink-0 items-center gap-2 border-b border-(--schemes-border-neutral)",
          lg ? "px-4 py-3" : "px-3 py-2",
        )}
      >
        <Search
          size={lg ? 18 : 14}
          strokeWidth={2}
          className="shrink-0 text-(--schemes-muted)"
        />
        <input
          autoFocus={!lg}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={`Search ${label.toLowerCase()}…`}
          className={clsx(
            "w-full bg-transparent text-(--schemes-ink) placeholder:text-(--schemes-muted) focus:outline-none",
            lg ? "text-base" : "text-xs",
          )}
        />
        {active && (
          <button
            type="button"
            onClick={() => onChange(new Set())}
            className={clsx(
              "shrink-0 font-semibold text-(--schemes-blue-600) hover:text-(--schemes-blue-900)",
              lg ? "text-sm" : "text-[11px]",
            )}
          >
            Clear
          </button>
        )}
      </div>
      <div
        className={clsx(
          "thin-scrollbar min-h-0 flex-1 overflow-y-auto",
          lg ? "p-2" : "p-1",
        )}
      >
        {visible.length === 0 ? (
          <p
            className={clsx(
              "text-center text-(--schemes-muted)",
              lg ? "px-2 py-6 text-sm" : "px-2 py-3 text-xs",
            )}
          >
            No matches
          </p>
        ) : (
          visible.map((option) => {
            const isOn = selected.has(option);
            return (
              <button
                type="button"
                key={option}
                onClick={() => toggle(option)}
                className={clsx(
                  "flex w-full items-center rounded-md text-left text-(--schemes-ink-soft) transition-colors hover:bg-(--schemes-blue-50)",
                  lg
                    ? "min-h-12 gap-3 px-3 text-base"
                    : "gap-2.5 px-2 py-1.5 text-xs",
                )}
              >
                <span
                  className={clsx(
                    "flex shrink-0 items-center justify-center rounded border transition-colors",
                    lg ? "size-5" : "size-4",
                    isOn
                      ? "border-(--schemes-blue-600) bg-(--schemes-blue-600) text-white"
                      : "border-(--schemes-border-neutral) bg-white",
                  )}
                >
                  {isOn && <Check size={lg ? 13 : 11} strokeWidth={3} />}
                </span>
                <span className="min-w-0 flex-1 truncate">
                  {formatOption(option)}
                </span>
              </button>
            );
          })
        )}
      </div>
    </>
  );
}

// A single removable filter dimension. Quiet ghost chip when empty; tinted with
// a count + clear (✕) when active. Opens a searchable, live multi-select panel:
// a popover on desktop, a bottom-sheet drawer on mobile (bigger tap targets).
function FilterChip({
  icon: Icon,
  label,
  unit,
  options,
  selected,
  onChange,
  formatOption = (v) => v,
}: FilterChipProps) {
  const isDesktop = useIsDesktop();
  const drawerState = useOverlayState();
  const active = selected.size > 0;

  const trigger = (
    <Button
      aria-label={`Filter by ${label}`}
      className={clsx(
        "inline-flex min-h-9 shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-[background-color,border-color,color]",
        active
          ? "border-(--schemes-blue-100) bg-(--schemes-blue-50) text-(--schemes-blue-600) pr-7"
          : "border-(--schemes-border-neutral) bg-transparent text-(--schemes-muted) hover:border-(--schemes-blue-100) hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-600)",
      )}
    >
      <Icon size={14} strokeWidth={2} className="shrink-0" />
      <span>{active ? `${selected.size} ${unit}` : label}</span>
      {!active && (
        <ChevronDown
          size={13}
          strokeWidth={2}
          className="shrink-0 opacity-70"
        />
      )}
    </Button>
  );

  // The clear (✕) sits beside the trigger as a separate control so it isn't
  // nested inside an interactive trigger.
  const clearButton = active && (
    <button
      type="button"
      aria-label={`Clear ${label} filter`}
      onClick={() => onChange(new Set())}
      className="absolute right-2 top-1/2 flex size-4 -translate-y-1/2 items-center justify-center rounded-full text-(--schemes-blue-600) transition-colors hover:bg-(--schemes-blue-100)"
    >
      <X size={12} strokeWidth={2.5} />
    </button>
  );

  return (
    <div className="relative flex shrink-0 items-center">
      {isDesktop ? (
        <Popover>
          {trigger}
          <Popover.Content
            placement="bottom start"
            className="z-50 w-[min(80vw,280px)] rounded-xl border border-(--schemes-border) bg-(--schemes-surface) p-0 shadow-sm"
          >
            <Popover.Dialog className="m-0 flex max-h-[60vh] flex-col p-0 outline-none">
              <FilterPanel
                label={label}
                options={options}
                selected={selected}
                onChange={onChange}
                formatOption={formatOption}
                size="sm"
              />
            </Popover.Dialog>
          </Popover.Content>
        </Popover>
      ) : (
        <Drawer state={drawerState}>
          {trigger}
          {/* Backdrop is the dark scrim AND the overlay that hosts the sheet —
              Content must nest inside it. The dim signals the page is still
              there (tap to dismiss), not a new screen. */}
          <Drawer.Backdrop className="bg-black/50">
            {/* Content is the full-screen overlay (its theme aligns children to
                the bottom). It must stay transparent — a background here would
                paint over the whole screen and hide the scrim. The surface +
                rounding live on the Dialog, which is the actual 80%-tall sheet:
                a plain flex column we control end-to-end (handle + heading,
                scrollable list, pinned Done). We avoid Drawer.Footer/Heading/
                CloseTrigger slots because their theme absolutely-positions them
                to the top of the sheet. */}
            <Drawer.Content placement="bottom" className="bg-transparent">
              <Drawer.Dialog className="flex h-[80vh] flex-col rounded-t-2xl bg-(--schemes-surface) pt-3 outline-none">
                <Drawer.Handle />
                <h2 className="shrink-0 px-4 pb-2 pt-1 text-base font-semibold text-(--schemes-blue-900)">
                  {label}
                </h2>
                <FilterPanel
                  label={label}
                  options={options}
                  selected={selected}
                  onChange={onChange}
                  formatOption={formatOption}
                  size="lg"
                />
                <div className="shrink-0 border-t border-(--schemes-border-neutral) p-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))]">
                  <button
                    type="button"
                    onClick={() => drawerState.close()}
                    className="inline-flex min-h-12 w-full items-center justify-center rounded-lg bg-(--schemes-blue-600) text-sm font-semibold text-white transition-colors hover:bg-(--schemes-blue-800)"
                  >
                    Done
                  </button>
                </div>
              </Drawer.Dialog>
            </Drawer.Content>
          </Drawer.Backdrop>
        </Drawer>
      )}
      {clearButton}
    </div>
  );
}

function SchemesFilter({
  schemes,
  setFilterObj,
  selectedLocations,
  setSelectedLocations,
  selectedAgencies,
  setSelectedAgencies,
  resetFilters,
  className,
}: SchemesFilterProps) {
  const allLocations: string[] = useMemo(() => {
    const locationSet = new Set<string>();
    schemes.forEach((scheme) => {
      if (scheme.planningArea) {
        (parseArrayString(scheme.planningArea) ?? []).forEach((a) =>
          locationSet.add(a),
        );
      }
    });
    // Position 'No Location' first in the location list.
    if (locationSet.has("No Location")) {
      locationSet.delete("No Location");
      return ["No Location", ...Array.from(locationSet).sort()];
    }
    return Array.from(locationSet).sort();
  }, [schemes]);

  const allAgencies = useMemo(
    () =>
      Array.from(new Set(schemes.map((s) => s.agency).filter(Boolean))).sort(),
    [schemes],
  );

  // Each dimension's option list narrows by the other dimension's selection so
  // the choices stay relevant (a location only lists agencies present there).
  const locationOptions = useMemo(() => {
    if (selectedAgencies.size === 0) return allLocations;
    const set = new Set<string>();
    schemes.forEach((scheme) => {
      if (selectedAgencies.has(scheme.agency) && scheme.planningArea) {
        (parseArrayString(scheme.planningArea) ?? []).forEach((a) =>
          set.add(a),
        );
      }
    });
    return Array.from(set).sort();
  }, [selectedAgencies, allLocations, schemes]);

  const agencyOptions = useMemo(() => {
    if (selectedLocations.size === 0) return allAgencies;
    const set = new Set<string>();
    schemes.forEach((scheme) => {
      if (
        scheme.agency &&
        scheme.planningArea &&
        selectedLocations.intersection(
          new Set(parseArrayString(scheme.planningArea)),
        ).size > 0
      ) {
        set.add(scheme.agency);
      }
    });
    return Array.from(set).sort();
  }, [selectedLocations, allAgencies, schemes]);

  // Apply live: selecting in a chip immediately updates the results, so chips
  // and the list always reflect the same state (no separate Apply button).
  const applyLocations = (next: Set<string>) => {
    setSelectedLocations(next);
    if (next.size === 0 && selectedAgencies.size === 0) resetFilters();
    else setFilterObj({ planningArea: next, agency: selectedAgencies });
  };
  const applyAgencies = (next: Set<string>) => {
    setSelectedAgencies(next);
    if (next.size === 0 && selectedLocations.size === 0) resetFilters();
    else setFilterObj({ planningArea: selectedLocations, agency: next });
  };

  return (
    <div className={clsx("flex shrink-0 items-center gap-2", className)}>
      <FilterChip
        icon={MapPin}
        label="Location"
        unit="areas"
        options={locationOptions}
        selected={selectedLocations}
        onChange={applyLocations}
        formatOption={capitalize}
      />
      <FilterChip
        icon={Building2}
        label="Agency"
        unit="agencies"
        options={agencyOptions}
        selected={selectedAgencies}
        onChange={applyAgencies}
      />
    </div>
  );
}

export default SchemesFilter;
