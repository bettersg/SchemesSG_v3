"use client";
import { useChat } from "@/providers";
import clsx from "clsx";
import Link from "next/link";
import SchemeCard from "../schemes/scheme-card";
import { HTMLAttributes } from "react";

function CategoryTag({ label }: { label: string }) {
  const palettes = [
    "bg-[#E6F1FB] text-[#185FA5] border-[#B5D4F4]",
    "bg-[#FAEEDA] text-[#BA7517] border-[#FAC775]",
    "bg-[#EEEDFE] text-[#534AB7] border-[#CECBF6]",
    "bg-[#EAF3DE] text-[#3B6D11] border-[#C0DD97]",
  ];
  const idx = label.charCodeAt(0) % palettes.length;
  return (
    <span className={`inline-flex text-[10px] font-medium px-1.5 py-0.5 rounded-full border ${palettes[idx]} whitespace-nowrap`}>
      {label.trim()}
    </span>
  );
}

interface SchemesListProps {
  selectedSchemeId?: string | null;
  onSelectScheme: (schemeId: string) => void;
  className?: string;
}

export default function SchemesList({ selectedSchemeId, onSelectScheme, className }: SchemesListProps) {
  const { schemes } = useChat();

//   if (!schemes.length) return null;

  return (
    <div className={clsx("w-[260px] shrink-0 bg-white border-l border-[#e8eef6]", "md:flex flex-col overflow-hidden", className)}>
      {/* Header */}
      <div className="px-3.5 pt-3 pb-2.5 border-b border-[#eef2f7] shrink-0">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[#185FA5] mb-0.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#1D9E75] shrink-0" />
          {schemes.length} schemes found
        </div>
        <p className="text-[10px] text-[#B4B2A9]">Click any scheme to view details</p>
      </div>

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto p-2 thin-scrollbar flex flex-col gap-1">
        {schemes.map((scheme) => {
          return (
			<SchemeCard 
				key={scheme.schemeId}
				scheme={scheme}
				onSelect={() => onSelectScheme(scheme.schemeId)}
			/>
            // <button
            //   key={scheme.schemeId}
            //   onClick={() => onSelectScheme(scheme.schemeId)}
            //   className={`w-full text-left rounded-lg border-[1.5px] px-3 py-2.5 mb-1.5 transition-all relative ${
            //     isActive
            //       ? "border-[#378ADD] bg-[#E6F1FB]"
            //       : "border-[#e0eaf5] bg-white hover:border-[#B5D4F4] hover:bg-[#f0f6ff]"
            //   }`}
            // >
            //   {isActive && (
            //     <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#378ADD] rounded-l-lg" />
            //   )}
            //   <div className="text-[9.5px] text-[#B4B2A9] mb-0.5 truncate">{scheme.agency}</div>
            //   <div className="text-[11.5px] font-semibold text-[#042C53] leading-snug mb-1.5 line-clamp-2">
            //     {scheme.schemeName}
            //   </div>
            //   <div className="flex gap-1 flex-wrap">
            //     {types.map((t) => <CategoryTag key={t} label={t} />)}
            //   </div>
            // </button>
          );
        })}
      </div>

      {/* Footer */}
      {/* <Link
        href="/explore"
        className="block text-center py-2.5 text-[11px] text-[#378ADD] font-medium border-t border-[#eef2f7] hover:bg-[#f7f9fc] transition-colors shrink-0"
      >
        Browse all {totalCount} schemes →
      </Link> */}
    </div>
  );
}
