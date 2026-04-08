"use client";
import { useChat } from "@/providers";
import { Button, Popover } from "@heroui/react";
import { useEffect, useRef, useState } from "react";
import SchemesList from "./schemes-list";

function CategoryTag({ label }: { label: string }) {
  const palettes = [
    "bg-[#E6F1FB] text-[#185FA5] border-[#B5D4F4]",
    "bg-[#FAEEDA] text-[#BA7517] border-[#FAC775]",
    "bg-[#EEEDFE] text-[#534AB7] border-[#CECBF6]",
    "bg-[#EAF3DE] text-[#3B6D11] border-[#C0DD97]",
  ];
  const idx = label.charCodeAt(0) % palettes.length;
  return (
    <span
      className={`inline-flex text-[9px] font-medium px-1.5 py-0.5 rounded-full border ${palettes[idx]} whitespace-nowrap`}
    >
      {label.trim()}
    </span>
  );
}

interface SchemesPopoverButtonProps {
  selectedSchemeId?: string | null;
  onSelectScheme: (schemeId: string) => void;
}

export default function SchemesPopoverButton({
  selectedSchemeId,
  onSelectScheme,
}: SchemesPopoverButtonProps) {
  const { schemes } = useChat();
  const [isOpen, setIsOpen] = useState(false);
  const [hasNewSchemes, setHasNewSchemes] = useState(false);
  const prevCountRef = useRef(schemes.length);

  useEffect(() => {
    if (schemes.length !== prevCountRef.current && schemes.length > 0) {
      setHasNewSchemes(true);
      prevCountRef.current = schemes.length;
    }
  }, [schemes]);

  useEffect(() => {
	if (!selectedSchemeId) {
		setIsOpen(true)
	}
  }, [selectedSchemeId])

  if (!schemes.length) return null;

  const handleSelect = (schemeId: string) => {
    onSelectScheme(schemeId);
    setIsOpen(false);
    setHasNewSchemes(false);
	window.history.replaceState(null, '', `/schemes/${schemeId}`)
  };
  
  return (
    <Popover
      isOpen={isOpen}
      onOpenChange={(open) => {
        setIsOpen(open);
        if (!open) setHasNewSchemes(false);
      }}
    >
        {/* Trigger button */}
        <Button
          className="relative inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#E6F1FB] border-[1.5px] border-[#B5D4F4] rounded-full text-[11px] font-semibold text-[#185FA5] hover:bg-[#d4e9f9] transition-colors"
        >
          <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
            <rect x="1" y="1" width="4" height="4" rx="1" stroke="#185FA5" strokeWidth="1.2" />
            <rect x="7" y="1" width="4" height="4" rx="1" stroke="#185FA5" strokeWidth="1.2" />
            <rect x="1" y="7" width="4" height="4" rx="1" stroke="#185FA5" strokeWidth="1.2" />
            <rect x="7" y="7" width="4" height="4" rx="1" stroke="#185FA5" strokeWidth="1.2" />
          </svg>
          Schemes
          {/* Badge */}
          <span
            className={`absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 bg-[#EF9F27] text-white text-[8px] font-bold rounded-full flex items-center justify-center border-2 border-white leading-none transition-transform ${
              hasNewSchemes ? "scale-125" : "scale-100"
            }`}
          >
            {schemes.length > 99 ? "99+" : schemes.length}
          </span>
        </Button>
      <Popover.Content className="p-0 w-[288px] rounded-xl shadow-[0_8px_32px_rgba(4,44,83,0.18)] overflow-hidden md:hidden"
      	placement="bottom end"
		style={{zIndex: 20}}
	  >
        <Popover.Dialog className="h-[320px] overflow-y-auto thin-scrollbar p-0 m-auto">
			{/* Popover header */}
			{/* <Popover.Heading>
				<div className="flex items-center justify-end px-3.5 py-2.5 border-b border-[#eef2f7]">
					<div className="flex items-center gap-1.5 text-[11px] font-semibold text-[#185FA5]">
					<span className="w-1.5 h-1.5 rounded-full bg-[#1D9E75]" />
					{totalCount} schemes found
					</div>
					<button
					onClick={() => setIsOpen(false)}
					className="w-5 h-5 rounded-full bg-[#F1EFE8] flex items-center justify-center text-[#5F5E5A] text-[10px] hover:bg-[#D3D1C7] transition-colors"
					>
					✕
					</button>
				</div>
			</Popover.Heading> */}
			<SchemesList selectedSchemeId={selectedSchemeId} onSelectScheme={handleSelect} className="flex"/>
		</Popover.Dialog>
      </Popover.Content>
    </Popover>
  );
}



// {/* <div>
// 				{/* Scheme list */}
// 				<div className="max-h-[320px] overflow-y-auto thin-scrollbar p-1.5">
// 				  {schemes.map((scheme) => {
// 					return (
// 						<SchemeCard
// 							key={scheme.schemeId}
// 							scheme={scheme}
// 							onSelect={() => handleSelect(scheme.schemeId)}
// 						/>
// 					);
// 				  })}
// 				</div>
// 				{/* Footer */}
// 				<Link
// 					href="/explore"
// 					className="block text-center py-2.5 text-[11px] text-[#378ADD] font-medium border-t border-[#eef2f7] hover:bg-[#f7f9fc] transition-colors shrink-0"
// 				>
// 					Browse all {totalCount} schemes →
// 				</Link>
// 			</div> */}