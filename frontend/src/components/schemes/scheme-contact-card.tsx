import { BranchContact } from "@/app/schemes/[schemeId]/page";
import { LocationIcon } from "@/assets/icons/location-icon";
import { MailIcon } from "@/assets/icons/mail-icon";
import { PhoneIcon } from "@/assets/icons/phone-icon";
import { Button, Card, Link } from "@heroui/react";

interface SchemeContactCardProps {
  contact: BranchContact;
}

export default function SchemeContactCard({contact}: SchemeContactCardProps) {
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
            <p>{email}</p>
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
