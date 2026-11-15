import { ReactNode } from "react";
import { I18nProvider } from "@lingui/react";
import { i18n } from "@/i18n/lingui";

export function I18nWrapper({ children }: { children: ReactNode }) {
  return <I18nProvider i18n={i18n}>{children}</I18nProvider>;
}
