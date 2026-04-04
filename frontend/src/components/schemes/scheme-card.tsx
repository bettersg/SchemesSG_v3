<<<<<<< HEAD
import Link from "next/link";
import { SearchResScheme } from "./schemes-list";
import { Card, CardBody, CardHeader, Chip, Image, Spacer } from "@heroui/react";

interface SchemeCardProps {
  scheme: SearchResScheme;
}

function SchemeCard({scheme}: SchemeCardProps) {
  return (
    <Link
      href={`/schemes/${scheme.schemeId}`}
      className="w-full"
      target="_blank"
      draggable="false"
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
              wrapper: 'shrink-0',
              img: 'object-contain'
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
=======
import Link from "next/link";
import { SearchResScheme } from "@/types/types";
import { Card, Chip } from "@heroui/react";
import Image from "next/image";
import { useState } from "react";

interface SchemeCardProps {
  scheme: SearchResScheme;
  onSelect: () => void;
}

function SchemeCard({ scheme, onSelect }: SchemeCardProps) {
  const types = scheme.schemeType.slice(0, 2);
  return (
	<button
	  onClick={onSelect}
	  className="shrink-0 text-left bg-white border border-[#e4edf7] rounded-xl p-4 hover:border-[#B5D4F4] hover:shadow-[0_2px_12px_rgba(24,95,165,0.1)] hover:-translate-y-0.5 transition-all group relative overflow-hidden"
	>
	  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#378ADD] opacity-0 group-hover:opacity-100 transition-opacity rounded-l-xl" />
	  <div className="flex gap-2.5 items-start mb-2.5">
		<AgencyLogo agency={scheme.agency} image={scheme.image} />
		<div className="flex-1 min-w-0">
		  <p className="text-[12.5px] font-semibold text-[#042C53] leading-snug line-clamp-2">{scheme.schemeName}</p>
		  <p className="text-[10.5px] text-[#B4B2A9] mt-0.5">{scheme.agency}</p>
		</div>
	  </div>
	  <div className="flex gap-1 flex-wrap mb-2">
		{types.map((t) => <CategoryTag key={t} label={t} />)}
	  </div>
	  <p className="text-xs text-[#5F5E5A] leading-relaxed line-clamp-2">{scheme.summary || scheme.description}</p>
	</button>
  );
}

function AgencyLogo({ agency, image }: { agency: string; image?: string }) {
	const [imageError, setImageError] = useState(false)
	if (!imageError) {
		return <img className="w-8 h-8" src={image} alt={`${agency} image`} onError={() => setImageError(true)}/>
	}
  const initials = agency.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase();
  return (
    <div className="w-8 h-8 rounded-lg bg-[#E6F1FB] border border-[#B5D4F4] flex items-center justify-center text-[10px] font-bold text-[#185FA5] shrink-0">
      {initials}
    </div>
  );
}

function CategoryTag({ label }: { label: string }) {
  const palettes = [
	"bg-[#E6F1FB] text-[#185FA5] border-[#B5D4F4]",
	"bg-[#FAEEDA] text-[#BA7517] border-[#FAC775]",
	"bg-[#EEEDFE] text-[#534AB7] border-[#CECBF6]",
	"bg-[#EAF3DE] text-[#3B6D11] border-[#C0DD97]",
  ];
  const idx = label.charCodeAt(0) % palettes.length;
  return (
	<Chip className={`inline-flex text-[10px] font-medium rounded-full border ${palettes[idx]} whitespace-nowrap`} size="sm">
	  {label.trim()}
	</Chip>
  );
}

export default SchemeCard;
>>>>>>> 5bcdda1 (New design initial draft)
