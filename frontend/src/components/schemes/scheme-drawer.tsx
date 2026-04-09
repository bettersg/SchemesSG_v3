"use client";
import { fetchWithAuth } from "@/lib/api";
import { parseArrayString } from "@/lib/utils";
import { BranchContact, SearchResScheme } from "@/types/types";
import Link from "next/link";
import { Drawer, Spinner, useOverlayState } from "@heroui/react";
import { useEffect, useState } from "react";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import SchemeLogo from "./scheme-logo";
import { getSchemes } from "@/lib/schemes";
import { useSchemes } from "@/providers";
import SchemeContent from "./scheme-content";

// interface DrawerScheme {
//   scheme: string;
//   schemeName: string;
//   agency: string;
//   schemeType?: string[];
//   description?: string;
//   targetAudience?: string[];
//   benefits?: string[];
//   eligibilityText?: string;
//   howToApply?: string;
//   link?: string;
//   contact?: BranchContact[];
// }

interface SchemeDrawerProps {
  scheme: SearchResScheme | null;
  onClose: () => void;
}

function useIsDesktop() {
  const [isDesktop, setIsDesktop] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    setIsDesktop(mq.matches);
    const handler = (e: MediaQueryListEvent) => setIsDesktop(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);
  return isDesktop;
}

export default function SchemeDrawer({ scheme, onClose }: SchemeDrawerProps) {
  const [isLoading, setIsLoading] = useState(false);
  const drawerState = useOverlayState({ defaultOpen: false });
  const isDesktop = useIsDesktop();

  useEffect(() => {
    if (scheme) {
      drawerState.open();
      // setIsLoading(true);
      // fetchWithAuth(
      //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes/${scheme}`,
      // )
      //   .then((r) => r.json())
      //   .then((res) => {
      //     const d = res.data;
      //     if (!d) return;
      //     const contacts: BranchContact[] = [];
      //     const areas = parseArrayString(d.planning_area);
      //     const phones = parseArrayString(d.phone);
      //     const emails = parseArrayString(d.email);
      //     const addresses = parseArrayString(d.address);
      //     if (areas && areas.length > 0) {
      //       areas.forEach((area: string, i: number) => {
      //         contacts.push({
      //           planningArea: area,
      //           phones: phones
      //             ? [phones[Math.min(i, phones.length - 1)]]
      //             : undefined,
      //           emails: emails
      //             ? [emails[Math.min(i, emails.length - 1)]]
      //             : undefined,
      //           address: addresses ? addresses[i] : undefined,
      //         });
      //       });
      //     } else if (phones || emails) {
      //       contacts.push({
      //         phones: phones || undefined,
      //         emails: emails || undefined,
      //       });
      //     }
      //     setScheme({
      //       scheme,
      //       schemeName: d.scheme || "",
      //       agency: d.agency || "",
      //       schemeType: d.scheme_type || "",
      //       description: d.llm_description || d.description || "",
      //       targetAudience: d.who_is_it_for || "",
      //       benefits: d.what_it_gives || "",
      //       eligibilityText: d.eligibility || "",
      //       howToApply: d.how_to_apply || "",
      //       link: d.link || "",
      //       contact: contacts,
      //     });
      //   })
      //   .catch(console.error)
      //   .finally(() => setIsLoading(false));
    } else {
      drawerState.close();
    }
  }, [scheme]);

  const handleClose = () => {
    onClose();
    drawerState.close();
  };

  /* Desktop View: Side panel with no backdrop */
  if (isDesktop)
    return (
      <AnimatePresence>
        {scheme && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="absolute inset-0 z-20 hidden lg:block"
              onClick={onClose}
            >
              {/* ── DESKTOP: left-side panel ── */}
              <motion.div
                initial={{ x: "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: "-100%" }}
                transition={{ type: "spring", stiffness: 340, damping: 34 }}
                className="h-full absolute top-0 left-0 bottom-0 w-[380px] lg:w-full bg-white z-30 overflow-y-auto thin-scrollbar hidden lg:flex flex-col"
              >
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 w-8 h-8 rounded-full bg-black/6 hover:bg-black/10 flex items-center justify-center text-[#5F5E5A] transition-colors z-50"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path
                      d="M1 1l10 10M11 1L1 11"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </button>
                <SchemeContent
                  scheme={scheme}
                />
              </motion.div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    );

  /* Mobile View: Bottom drawer with translucent backdrop */
  return (
    <Drawer
      state={drawerState}
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          handleClose();
        }
      }}
    >
      <Drawer.Backdrop variant="transparent" className="bg-black/10">
        <Drawer.Content placement={isDesktop ? "left" : "bottom"}>
          <Drawer.Dialog
            className={clsx(
              "h-full p-0 overflow-hidden",
              isDesktop ? "w-1/2" : "w-full",
            )}
          >
            <Drawer.CloseTrigger className="absolute z-50" />
            {!isDesktop && (
              <Drawer.Handle className="absolute left-1/2 top-3 z-50" />
            )}
            <Drawer.Body className="p-0">
              <SchemeContent
                scheme={scheme}
              />
            </Drawer.Body>
          </Drawer.Dialog>
        </Drawer.Content>
      </Drawer.Backdrop>
    </Drawer>
  );
}
