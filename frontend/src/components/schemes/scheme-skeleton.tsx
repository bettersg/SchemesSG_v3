"use client";

import { Skeleton } from "@heroui/react";
import {
  productCardPadded,
  productPageContent,
  productPageShell,
} from "@/lib/design-system/product-styles";

function SectionLabelSkeleton() {
  return (
    <div className="mb-3 flex items-center gap-2">
      <Skeleton className="h-2 w-2 rounded-[3px]" />
      <Skeleton className="h-3 w-24 rounded-full" />
    </div>
  );
}

function CheckItemSkeleton({ width = "w-40" }: { width?: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <Skeleton className="mt-0.5 h-[18px] w-[18px] shrink-0 rounded-[5px]" />
      <Skeleton className={`h-4 ${width} rounded-full`} />
    </div>
  );
}

function MarkdownSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className={`h-4 rounded-full ${
            index === lines - 1 ? "w-4/5" : "w-full"
          }`}
        />
      ))}
    </div>
  );
}

export default function SchemeSkeleton() {
  return (
    <div className={productPageShell}>
      <div className={productPageContent}>
        <div className="mb-8 flex flex-col items-center gap-4 text-center sm:flex-row sm:items-start sm:text-left">
          <Skeleton className="h-18 w-18 shrink-0 rounded-lg" />
          <div className="flex w-full max-w-md flex-col items-center gap-2 sm:items-start">
            <Skeleton className="h-8 w-48 rounded-full sm:h-9 sm:w-64" />
            <Skeleton className="h-5 w-64 max-w-full rounded-full" />
            <Skeleton className="h-5 w-32 rounded-full" />
          </div>
        </div>

        <div className={`${productCardPadded} mb-6`}>
          <SectionLabelSkeleton />
          <MarkdownSkeleton lines={4} />
        </div>

        <div className={`${productCardPadded} mb-6`}>
          <div className="mb-5 flex items-center gap-2">
            <Skeleton className="h-7 w-24 rounded-full" />
          </div>

          <div className="flex flex-col gap-8 lg:flex-row">
            <div className="flex flex-[2] flex-col gap-6">
              <div className="flex flex-col gap-6 sm:flex-row">
                <div className="flex-1">
                  <SectionLabelSkeleton />
                  <div className="flex flex-col gap-2">
                    <CheckItemSkeleton width="w-44" />
                    <CheckItemSkeleton width="w-52" />
                    <CheckItemSkeleton width="w-36" />
                  </div>
                </div>
                <div className="flex-1">
                  <SectionLabelSkeleton />
                  <div className="flex flex-col gap-2">
                    <CheckItemSkeleton width="w-48" />
                    <CheckItemSkeleton width="w-40" />
                    <CheckItemSkeleton width="w-56" />
                  </div>
                </div>
              </div>

              <div>
                <SectionLabelSkeleton />
                <MarkdownSkeleton lines={3} />
              </div>

              <div>
                <SectionLabelSkeleton />
                <MarkdownSkeleton lines={4} />
              </div>
            </div>

            <div className="flex flex-1 flex-col gap-6">
              <div>
                <SectionLabelSkeleton />
                <div className="flex flex-wrap gap-1.5">
                  <Skeleton className="h-5 w-24 rounded-full" />
                  <Skeleton className="h-5 w-28 rounded-full" />
                  <Skeleton className="h-5 w-20 rounded-full" />
                </div>
              </div>

              <div>
                <SectionLabelSkeleton />
                <Skeleton className="h-4 w-40 rounded-full" />
              </div>

              <div>
                <SectionLabelSkeleton />
                <div className="flex flex-col gap-3">
                  {Array.from({ length: 2 }).map((_, index) => (
                    <div
                      key={index}
                      className="flex flex-col gap-1.5 rounded-xl border border-(--schemes-border) bg-(--schemes-bg) p-3.5"
                    >
                      <Skeleton className="h-3 w-28 rounded-full" />
                      <Skeleton className="h-4 w-full rounded-full" />
                      <Skeleton className="h-4 w-32 rounded-full" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap justify-center gap-3 border-t border-(--schemes-border) pt-5 sm:justify-end">
            <Skeleton className="h-12 w-36 rounded-lg" />
            <Skeleton className="h-12 w-48 rounded-lg" />
          </div>
        </div>

        <section className="mb-8 rounded-xl border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-4">
          <div className="flex items-start gap-3">
            <Skeleton className="mt-0.5 h-[18px] w-[18px] shrink-0 rounded-full" />
            <div className="flex-1">
              <Skeleton className="mb-2 h-4 w-40 rounded-full" />
              <Skeleton className="h-4 w-full rounded-full" />
              <Skeleton className="mt-2 h-4 w-4/5 rounded-full" />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
