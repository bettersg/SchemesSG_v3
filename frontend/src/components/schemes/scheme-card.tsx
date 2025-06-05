import Link from "next/link";
import { SearchResScheme } from "./schemes-list";
import { Card, CardBody, CardHeader, Chip, Image, Spacer } from "@nextui-org/react";

interface SchemeCardProps {
  scheme: SearchResScheme;
}

function SchemeCard({scheme}: SchemeCardProps) {
  return (
    <Link
      href={`/schemes/${scheme.schemeId}`}
      className="w-full"
      target="_blank"
    >
      <Card shadow="sm" className="w-full h-full" isHoverable>
        <CardHeader className="flex gap-3 font-semibold">
          <Image
            src={scheme.image}
            alt={`${scheme.agency} logo`}
            height={60}
            width={60}
            radius="sm"
            classNames={{
              wrapper: 'shrink-0'
            }}
          />
          <div className="flex flex-col">
              <p className="text-md">{scheme.schemeName}</p>
              <p className="text-small text-default-500">{scheme.agency}</p>
          </div>
        </CardHeader>
        <CardBody>
          <div className="flex flex-wrap gap-2 h-[1lh] overflow-y-hidden">
            {scheme.schemeType && scheme.schemeType.split(",").slice(0,3).map((type) => (
              <Chip
                key={type}
                size="sm"
                radius="sm"
                color="primary"
                variant="flat"
              >
                {type.trim()}
              </Chip>
            ))}
          </div>
          <Spacer y={2}/>
          <p className="text-small">
            {scheme.summary}
          </p>
        </CardBody>
      </Card>
    </Link>
  );
}

export default SchemeCard;