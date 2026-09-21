import { Mail, MapPin, Phone } from "lucide-react";
import { BranchContact } from "@/types/types";
import { capitalize } from "@/lib/utils";

interface AgencyContactCardProps {
  contact: BranchContact;
  schemeName: string;
  agency: string;
}

export default function AgencyContactCard({
  contact,
  schemeName,
  agency,
}: AgencyContactCardProps) {
  const { planningArea, address, phones, emails } = contact;

  const mapsLabel =
    address ??
    `${capitalize(planningArea ? planningArea.toLowerCase() : agency)} branch`;

  return (
    <div className="flex flex-col gap-2 rounded-xl border border-(--schemes-blue-100) bg-(--schemes-surface) p-4 text-sm text-(--schemes-muted)">
      {planningArea && (
        <p className="text-xs font-semibold tracking-wide text-(--schemes-blue-900) uppercase">
          {planningArea}
        </p>
      )}
      {address && (
        <a
          href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${schemeName} ${address}`)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-(--schemes-muted) hover:text-(--schemes-blue-600)"
        >
          <MapPin size={16} strokeWidth={2} className="shrink-0" />
          {mapsLabel}
        </a>
      )}
      {phones?.map((p) => (
        <a
          key={p}
          href={`tel:${p}`}
          className="flex items-center gap-2 text-(--schemes-blue-600) hover:underline"
        >
          <Phone size={16} strokeWidth={2} className="shrink-0" />
          {p}
        </a>
      ))}
      {emails?.map((e) => (
        <a
          key={e}
          href={`mailto:${e}`}
          className="flex items-center gap-2 break-all text-(--schemes-blue-600) hover:underline"
        >
          <Mail size={16} strokeWidth={2} className="shrink-0" />
          {e}
        </a>
      ))}
    </div>
  );
}
