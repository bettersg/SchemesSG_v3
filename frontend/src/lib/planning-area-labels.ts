import type { I18n, MessageDescriptor } from "@lingui/core";
import { msg } from "@lingui/core/macro";
import { formatPlanningArea, PLANNING_AREAS } from "@/lib/catalog-filters";

/**
 * Display names for the planning areas. The upper-case keys stay as they are:
 * they are the filter values the catalog API and the URLs use.
 */
export const PLANNING_AREA_LABELS: Record<
  (typeof PLANNING_AREAS)[number],
  MessageDescriptor
> = {
  "ANG MO KIO": msg({
    message: "Ang Mo Kio",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "BEDOK": msg({
    message: "Bedok",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "BISHAN": msg({
    message: "Bishan",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "BOON LAY": msg({
    message: "Boon Lay",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "BUKIT BATOK": msg({
    message: "Bukit Batok",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "BUKIT MERAH": msg({
    message: "Bukit Merah",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "BUKIT PANJANG": msg({
    message: "Bukit Panjang",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "BUKIT TIMAH": msg({
    message: "Bukit Timah",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "CENTRAL WATER CATCHMENT": msg({
    message: "Central Water Catchment",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "CHANGI": msg({
    message: "Changi",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "CHANGI BAY": msg({
    message: "Changi Bay",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "CHOA CHU KANG": msg({
    message: "Choa Chu Kang",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "CLEMENTI": msg({
    message: "Clementi",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "DOWNTOWN CORE": msg({
    message: "Downtown Core",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "GEYLANG": msg({
    message: "Geylang",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "HOUGANG": msg({
    message: "Hougang",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "JURONG EAST": msg({
    message: "Jurong East",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "JURONG WEST": msg({
    message: "Jurong West",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "KALLANG": msg({
    message: "Kallang",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "LIM CHU KANG": msg({
    message: "Lim Chu Kang",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "MANDAI": msg({
    message: "Mandai",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "MARINA EAST": msg({
    message: "Marina East",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "MARINA SOUTH": msg({
    message: "Marina South",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "MARINE PARADE": msg({
    message: "Marine Parade",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "MUSEUM": msg({
    message: "Museum",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "NEWTON": msg({
    message: "Newton",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "NORTH-EASTERN ISLANDS": msg({
    message: "North-Eastern Islands",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "NOVENA": msg({
    message: "Novena",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "ORCHARD": msg({
    message: "Orchard",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "OUTRAM": msg({
    message: "Outram",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "PASIR RIS": msg({
    message: "Pasir Ris",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "PAYA LEBAR": msg({
    message: "Paya Lebar",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "PIONEER": msg({
    message: "Pioneer",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "PUNGGOL": msg({
    message: "Punggol",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "QUEENSTOWN": msg({
    message: "Queenstown",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "RIVER VALLEY": msg({
    message: "River Valley",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "ROCHOR": msg({
    message: "Rochor",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "SELETAR": msg({
    message: "Seletar",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "SEMBAWANG": msg({
    message: "Sembawang",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "SENGKANG": msg({
    message: "Sengkang",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "SERANGOON": msg({
    message: "Serangoon",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "SIMPANG": msg({
    message: "Simpang",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "SINGAPORE RIVER": msg({
    message: "Singapore River",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "SOUTHERN ISLANDS": msg({
    message: "Southern Islands",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "STRAITS VIEW": msg({
    message: "Straits View",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "SUNGEI KADUT": msg({
    message: "Sungei Kadut",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "TAMPINES": msg({
    message: "Tampines",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "TANGLIN": msg({
    message: "Tanglin",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "TENGAH": msg({
    message: "Tengah",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "TOA PAYOH": msg({
    message: "Toa Payoh",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "TUAS": msg({
    message: "Tuas",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "WESTERN ISLANDS": msg({
    message: "Western Islands",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "WESTERN WATER CATCHMENT": msg({
    message: "Western Water Catchment",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "WOODLANDS": msg({
    message: "Woodlands",
    comment: "Singapore URA planning area name; use its official local name",
  }),
  "YISHUN": msg({
    message: "Yishun",
    comment: "Singapore URA planning area name; use its official local name",
  }),
};

/** Translated name for a planning area value, title-cased if it is unknown. */
export function planningAreaLabel(i18n: I18n, area: string) {
  const descriptor =
    PLANNING_AREA_LABELS[area.toUpperCase() as keyof typeof PLANNING_AREA_LABELS];
  return descriptor ? i18n._(descriptor) : formatPlanningArea(area);
}
