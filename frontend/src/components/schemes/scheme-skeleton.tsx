"use client";

import { Skeleton } from "@heroui/react";
import PageShell from "@/components/layout/page-shell";
import {
  productCardPadded,
  productSegmentedList,
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
      <Skeleton className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full" />
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
    <PageShell contentClassName="pb-24 md:pb-8">
      <div className="sticky top-0 z-20 -mt-8 mb-8 ml-[calc(50%-50vw)] w-screen border-b border-(--schemes-border-neutral) bg-(--schemes-surface) px-4 sm:px-6 md:mx-auto md:w-full md:max-w-3xl">
        <div className="py-3">
          <div className="flex items-center justify-between gap-4 text-left">
            <div className="flex min-w-0 items-center gap-4 md:gap-5">
              <Skeleton className="h-16 w-16 shrink-0 rounded-lg" />
              <div className="flex min-w-0 flex-1 flex-col gap-2">
                <Skeleton className="h-3 w-32 rounded-full" />
                <Skeleton className="h-6 w-56 max-w-full rounded-full md:w-80" />
                <Skeleton className="h-4 w-64 max-w-full rounded-full md:w-[28rem]" />
              </div>
            </div>

            <div className="hidden w-full max-w-52 flex-col gap-2 md:flex">
              <Skeleton className="h-11 w-full rounded-lg" />
              <Skeleton className="h-11 w-full rounded-lg" />
            </div>
          </div>
        </div>

        <div className="border-t border-(--schemes-border-neutral) py-3">
          <div
            className={`${productSegmentedList} no-scrollbar flex w-max min-w-full gap-1 overflow-x-auto`}
          >
            <Skeleton className="h-11 w-24 shrink-0 rounded-lg" />
            <Skeleton className="h-11 w-32 shrink-0 rounded-lg" />
            <Skeleton className="h-11 w-28 shrink-0 rounded-lg" />
            <Skeleton className="h-11 w-32 shrink-0 rounded-lg" />
          </div>
        </div>
      </div>

      <section className={`${productCardPadded} mx-auto mb-8 max-w-3xl`}>
        <Skeleton className="mb-4 h-6 w-28 rounded-full" />
        <div className="flex flex-col gap-6">
          <div>
            <SectionLabelSkeleton />
            <MarkdownSkeleton lines={4} />
          </div>
          <div>
            <SectionLabelSkeleton />
            <div className="flex flex-wrap gap-2">
              <Skeleton className="h-6 w-28 rounded-full" />
              <Skeleton className="h-6 w-24 rounded-full" />
              <Skeleton className="h-6 w-32 rounded-full" />
            </div>
          </div>
        </div>
      </section>

      <section className={`${productCardPadded} mx-auto mb-8 max-w-3xl`}>
        <Skeleton className="mb-4 h-6 w-36 rounded-full" />
        <div className="flex flex-col gap-8">
          <div className="flex flex-col gap-6 lg:flex-row">
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
        </div>
      </section>

      <section className={`${productCardPadded} mx-auto mb-8 max-w-3xl`}>
        <Skeleton className="mb-4 h-6 w-32 rounded-full" />
        <MarkdownSkeleton lines={4} />
      </section>

      <section className={`${productCardPadded} mx-auto mb-8 max-w-3xl`}>
        <Skeleton className="mb-4 h-6 w-36 rounded-full" />
        <div className="flex flex-col gap-6">
          <div>
            <SectionLabelSkeleton />
            <Skeleton className="h-4 w-48 rounded-full" />
          </div>

          <div>
            <SectionLabelSkeleton />
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {Array.from({ length: 2 }).map((_, index) => (
                <div
                  key={index}
                  className="flex flex-col gap-2 rounded-xl border border-(--schemes-blue-100) bg-(--schemes-surface) p-4"
                >
                  <Skeleton className="h-3 w-28 rounded-full" />
                  <Skeleton className="h-4 w-full rounded-full" />
                  <Skeleton className="h-4 w-32 rounded-full" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto mb-8 max-w-3xl rounded-xl border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-6">
        <div className="flex items-start gap-4">
          <Skeleton className="mt-0.5 h-[18px] w-[18px] shrink-0 rounded-full" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-4 w-40 rounded-full" />
            <div>
              <Skeleton className="h-4 w-full rounded-full" />
              <Skeleton className="mt-2 h-4 w-4/5 rounded-full" />
            </div>
          </div>
        </div>
      </section>

      <div className="fixed right-0 bottom-0 left-0 z-30 border-t border-(--schemes-border-neutral) bg-(--schemes-surface) p-3 md:hidden">
        <div className="mx-auto grid max-w-sm grid-cols-2 gap-3">
          <Skeleton className="h-12 w-full rounded-lg" />
          <Skeleton className="h-12 w-full rounded-lg" />
        </div>
      </div>
    </PageShell>
  );
}
