"use client";

import { Button, Dropdown, Label, type Selection } from "@heroui/react";
import { ChevronDown, Globe } from "lucide-react";
import { useLanguage, type Locale } from "@/lib/landing-i18n";
import { cn } from "@/lib/utils";
import { cssTransition } from "@/lib/design-system/motion";
import { useLingui } from "@lingui/react/macro";

// Each language is named in its own script so people can find theirs.
const languages: { code: Locale; label: string; short: string }[] = [
  { code: "en", label: "English", short: "EN" },
  { code: "zh", label: "中文", short: "中文" },
  { code: "ms", label: "Melayu", short: "Melayu" },
  { code: "ta", label: "தமிழ்", short: "தமிழ்" },
];

export function LanguageToggle({ className }: { className?: string }) {
  const { locale, setLocale } = useLanguage();
  const { t } = useLingui();
  const current = languages.find((lang) => lang.code === locale) ?? languages[0];
  const currentLanguage = current.label;

  const onSelectionChange = (keys: Selection) => {
    if (keys === "all") return;
    const [code] = keys;
    if (code) setLocale(code as Locale);
  };

  return (
    <Dropdown>
      <Button
        aria-label={t({
          message: `Language: ${currentLanguage}`,
          comment: "Aria label for the navbar language menu button; the value is the current language name",
        })}
        className={cn(
          "min-h-11 gap-1.5 rounded-full border border-neutral-200/60 bg-neutral-100 px-3 text-sm font-medium text-neutral-900 shadow-none hover:bg-neutral-200/70 cursor-pointer",
          cssTransition.colorsState,
          className,
        )}
      >
        <Globe className="h-4 w-4 text-neutral-500" aria-hidden />
        <span>{current.short}</span>
        <ChevronDown className="h-3.5 w-3.5 text-neutral-500" aria-hidden />
      </Button>
      <Dropdown.Popover placement="bottom" className="min-w-40">
        <Dropdown.Menu
          aria-label={t({ message: "Select language", comment: "Aria label for the language selector toggle" })}
          selectionMode="single"
          disallowEmptySelection
          selectedKeys={new Set([locale])}
          onSelectionChange={onSelectionChange}
        >
          {languages.map((lang) => (
            <Dropdown.Item key={lang.code} id={lang.code} textValue={lang.label} lang={lang.code}>
              <Dropdown.ItemIndicator className="text-neutral-900" />
              <Label>{lang.label}</Label>
            </Dropdown.Item>
          ))}
        </Dropdown.Menu>
      </Dropdown.Popover>
    </Dropdown>
  );
}
