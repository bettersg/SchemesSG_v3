import { BranchContact } from "@/types/types";
import { Mail, MapPin, Phone } from "lucide-react";
import { Card, Link } from "@heroui/react";
import {
  productIconButton,
  productCard,
} from "@/lib/design-system/product-styles";

interface SchemeContactCardProps {
  contact: BranchContact;
}

export default function SchemeContactCard({ contact }: SchemeContactCardProps) {
  if (!contact.address && !contact.phones?.length && !contact.emails?.length) {
    return null;
  }

  return (
    <Card className={`${productCard} p-4 flex flex-col gap-2 shadow-none`}>
      {contact.address && (
        <div className="flex gap-2 justify-between">
          <p className="text-sm text-(--schemes-muted)">
            {contact.address}
          </p>
          <Link
            aria-label="Open address in maps"
            className={`${productIconButton} inline-flex items-center justify-center border border-(--schemes-blue-100) bg-white text-(--schemes-blue-600) hover:bg-(--schemes-blue-50)`}
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
              contact.address,
            )}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <MapPin size={20} strokeWidth={2} />
          </Link>
        </div>
      )}
      {contact.phones &&
        contact.phones.map((phone: string, index: number) => (
          <div key={index}>
            <div className="flex gap-2 justify-between">
              <p className="text-sm text-(--schemes-muted)">{phone}</p>
              <Link
                aria-label="phone"
                className={`${productIconButton} inline-flex items-center justify-center border border-(--schemes-blue-100) bg-white text-(--schemes-blue-600) hover:bg-(--schemes-blue-50)`}
                href={`tel:${phone}`}
              >
                <Phone size={20} strokeWidth={2} />
              </Link>
            </div>
          </div>
        ))}
      {contact.emails &&
        contact.emails.map((email: string, index: number) => (
          <div key={index} className="flex gap-2 justify-between">
            <p className="break-all max-w-[180px] sm:max-w-none text-sm text-(--schemes-muted)">
              {email}
            </p>
            <Link
              aria-label="email"
              className={`${productIconButton} inline-flex items-center justify-center border border-(--schemes-blue-100) bg-white text-(--schemes-blue-600) hover:bg-(--schemes-blue-50)`}
              href={`mailto:${email}`}
            >
              <Mail size={20} strokeWidth={2} />
            </Link>
          </div>
        ))}
    </Card>
  );
}
