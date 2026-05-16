"use client";

import { Button, Popover } from "@heroui/react";
import { LayoutGrid } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  productButtonSecondary,
  productButtonSm,
} from "@/lib/design-system/product-styles";
import { useChat } from "@/providers";
import SchemesList from "./schemes-list";

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
      setIsOpen(true);
    }
  }, [selectedSchemeId]);

  if (!schemes.length) return null;

  const handleSelect = (schemeId: string) => {
    onSelectScheme(schemeId);
    setIsOpen(false);
    setHasNewSchemes(false);
    window.history.replaceState(null, "", `/schemes/${schemeId}`);
  };

  return (
    <Popover
      isOpen={isOpen}
      onOpenChange={(open) => {
        setIsOpen(open);
        if (!open) setHasNewSchemes(false);
      }}
    >
      <Button
        variant="outline"
        className={`${productButtonSecondary} ${productButtonSm} relative text-[11px]`}
      >
        <LayoutGrid size={11} strokeWidth={1.6} />
        Schemes
        <span
          className={`absolute -top-1.5 -right-1.5 flex h-4 min-w-[16px] items-center justify-center rounded-full border-2 border-white bg-(--schemes-amber-400) px-1 text-[8px] leading-none font-semibold text-(--schemes-ink) transition-transform ${
            hasNewSchemes ? "scale-125" : "scale-100"
          }`}
        >
          {schemes.length > 99 ? "99+" : schemes.length}
        </span>
      </Button>
      <Popover.Content
        className="w-[288px] overflow-hidden rounded-xl p-0 shadow-[0_8px_32px_rgba(4,44,83,0.18)] md:hidden"
        placement="bottom end"
        style={{ zIndex: 20 }}
      >
        <Popover.Dialog className="thin-scrollbar m-auto h-[320px] overflow-y-auto p-0">
          <SchemesList
            selectedSchemeId={selectedSchemeId}
            onSelectScheme={handleSelect}
            className="flex"
          />
        </Popover.Dialog>
      </Popover.Content>
    </Popover>
  );
}
