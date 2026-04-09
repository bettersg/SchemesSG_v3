import Link from "next/link";
import { SearchResScheme } from "@/types/types";
import { Card, Chip } from "@heroui/react";
import Image from "next/image";
import { useState } from "react";
import clsx from "clsx";
import SchemeLogo from "./scheme-logo";

interface SchemeCardProps {
  scheme: SearchResScheme;
  onSelect: () => void;
  className?: string;
}

function SchemeCard({ scheme, onSelect, className }: SchemeCardProps) {
  const types = scheme.schemeType.slice(0, 2);
  return (
	<button
	  onClick={onSelect}
	  className={clsx("max-w-sm shrink-0 text-left bg-white border border-[#e4edf7] rounded-xl p-4 hover:border-[#B5D4F4] hover:shadow-[0_2px_12px_rgba(24,95,165,0.1)] hover:-translate-y-0.5 transition-all group relative overflow-hidden", className)}
	>
	  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#378ADD] opacity-0 group-hover:opacity-100 transition-opacity rounded-l-xl" />
	  <div className="flex gap-2.5 items-start mb-2.5">
		<SchemeLogo agency={scheme.agency} image={scheme.image} />
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