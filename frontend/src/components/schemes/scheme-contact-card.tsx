<<<<<<< HEAD
import { BranchContact } from "@/app/(main)/schemes/[schemeId]/page";
import { LocationIcon } from "@/assets/icons/location-icon";
import { MailIcon } from "@/assets/icons/mail-icon";
import { PhoneIcon } from "@/assets/icons/phone-icon";
import { Button, Card, Link } from "@heroui/react";

interface SchemeContactCardProps {
  contact: BranchContact;
}

export default function SchemeContactCard({contact}: SchemeContactCardProps) {
  if (!contact.address && !contact.phones?.length && !contact.emails?.length) {
    return null;
  }

  return (
    <Card
      className="p-4 flex flex-col gap-2"
      classNames={{
        base: "shadow-md",
      }}
    >
      {contact.address && (
        <div
          className="flex gap-2 justify-between"
        >
          <p>{contact.address}</p>
          <Button
            isIconOnly
            size="sm"
            aria-label="phone"
            color="primary"
            variant="light"
            as={Link}
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
              contact.address
            )}`}
            isExternal
          >
            <LocationIcon size={20} />
          </Button>
        </div>
      )}
      {contact.phones &&
        contact.phones.map((phone, index) => (
          <div key={index}>
            <div className="flex gap-2 justify-between">
              <p>{phone}</p>
              <Button
                isIconOnly
                size="sm"
                aria-label="phone"
                color="primary"
                variant="light"
                as={Link}
                href={`tel:${phone}`}
              >
                <PhoneIcon size={20} />
              </Button>
            </div>
          </div>
        ))}
      {contact.emails &&
        contact.emails.map((email, index) => (
          <div
            key={index}
            className="flex gap-2 justify-between"
          >
            <p className="break-all max-w-[180px] sm:max-w-none">{email}</p>
            <Button
              isIconOnly
              size="sm"
              aria-label="email"
              color="primary"
              variant="light"
              as={Link}
              href={`mailto:${email}`}
            >
              <MailIcon size={20} />
            </Button>
          </div>
        ))}
    </Card>
  );
}
=======
import { BranchContact } from "@/app/schemes/[schemeId]/page";
import { LocationIcon } from "@/assets/icons/location-icon";
import { MailIcon } from "@/assets/icons/mail-icon";
import { PhoneIcon } from "@/assets/icons/phone-icon";
import { Button, Card } from "@heroui/react";
import Link from "next/link";

interface SchemeContactCardProps {
  contact: BranchContact;
}

export default function SchemeContactCard({ contact }: SchemeContactCardProps) {
  return (
    <Card className="p-4 flex flex-col gap-2">
      <Card.Content className="shadow-md">
        {contact.address && (
          <div className="flex gap-2 justify-between">
            <p>{contact.address}</p>
            <Button isIconOnly size="sm" aria-label="map">
              <Link
                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(contact.address)}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                <LocationIcon size={20} />
              </Link>
            </Button>
          </div>
        )}
        {contact.phones?.map((phone, index) => (
          <div key={index} className="flex gap-2 justify-between">
            <p>{phone}</p>
            <Button isIconOnly size="sm" aria-label="phone" color="primary" variant="light">
              <Link href={`tel:${phone}`}>
                <PhoneIcon size={20} />
              </Link>
            </Button>
          </div>
        ))}
        {contact.emails?.map((email, index) => (
          <div key={index} className="flex gap-2 justify-between">
            <p className="break-all max-w-[180px] sm:max-w-none">{email}</p>
            <Button isIconOnly size="sm" aria-label="email" color="primary" variant="light">
              <Link href={`mailto:${email}`}>
                <MailIcon size={20} />
              </Link>
            </Button>
          </div>
        ))}
      </Card.Content>
    </Card>
  );
}
>>>>>>> 5bcdda1 (New design initial draft)
