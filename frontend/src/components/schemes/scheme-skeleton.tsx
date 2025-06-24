"use client";

import { Skeleton } from "@nextui-org/react";

export default function SchemeSkeleton() {
  return (
    <>
      {/* Header section */}
      <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 mb-8">
        <Skeleton className="w-32 h-32 rounded-md sm:mb-0 mb-3" />
        <div className="flex-1 flex flex-col items-center sm:items-start gap-2">
          <Skeleton className="h-8 w-40 mb-2 rounded-lg" />
          <Skeleton className="h-4 w-64 rounded-lg" />
          <div className="flex gap-2 mt-3">
            <Skeleton className="w-8 h-8 rounded-md" />
            <Skeleton className="w-8 h-8 rounded-md" />
            <Skeleton className="w-8 h-8 rounded-md" />
          </div>
        </div>
      </div>

      {/* Description section */}
      <div className="p-6 mt-4">
        <Skeleton className="h-7 w-32 mb-6 rounded-lg" />
        <Skeleton className="h-5 w-full mb-2 rounded-lg" />
        <Skeleton className="h-5 w-full mb-2 rounded-lg" />
        <Skeleton className="h-5 w-full mb-2 rounded-lg" />
        <Skeleton className="h-5 w-full mb-2 rounded-lg" />
      </div>

      {/* details section */}
      <div className="p-6 mt-4 sm:flex gap-7">
        {/* main */}
        <div className="flex-[2]">
          <Skeleton className="h-7 w-32 mb-6 rounded-lg" />

          <div className="mb-4">
            <Skeleton className="h-4 w-20 mb-2 rounded-lg" />
            <Skeleton className="h-6 w-48 rounded-lg" />
          </div>

          <div className="sm:flex justify-between mb-8">
            <div className="flex-1 sm:mb-0 mb-4">
              <Skeleton className="h-4 w-20 mb-3 rounded-lg" />
              <div className="pl-4 space-y-2">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-3 w-3 rounded-full" />
                  <Skeleton className="h-4 w-40 rounded-lg" />
                </div>
                <div className="flex items-center gap-2">
                  <Skeleton className="h-3 w-3 rounded-full" />
                  <Skeleton className="h-4 w-40 rounded-lg" />
                </div>
                <div className="flex items-center gap-2">
                  <Skeleton className="h-3 w-3 rounded-full" />
                  <Skeleton className="h-4 w-40 rounded-lg" />
                </div>
              </div>
            </div>
            <div className="flex-1">
              <Skeleton className="h-4 w-20 mb-3 rounded-lg" />
              <div className="pl-4 space-y-2">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-3 w-3 rounded-full" />
                  <Skeleton className="h-4 w-40 rounded-lg" />
                </div>
                <div className="flex items-center gap-2">
                  <Skeleton className="h-3 w-3 rounded-full" />
                  <Skeleton className="h-4 w-40 rounded-lg" />
                </div>
                <div className="flex items-center gap-2">
                  <Skeleton className="h-3 w-3 rounded-full" />
                  <Skeleton className="h-4 w-40 rounded-lg" />
                </div>
              </div>
            </div>
          </div>

          <div className="mb-4">
            <Skeleton className="h-4 w-20 mb-3 rounded-lg" />
            <Skeleton className="h-4 w-full mb-2 rounded-lg" />
            <Skeleton className="h-4 w-full mb-2 rounded-lg" />
            <Skeleton className="h-4 w-full mb-2 rounded-lg" />
          </div>

          <div className="mb-4">
            <Skeleton className="h-4 w-20 mb-3 rounded-lg" />
            <Skeleton className="h-4 w-full mb-2 rounded-lg" />
            <Skeleton className="h-4 w-full mb-2 rounded-lg" />
            <Skeleton className="h-4 w-full mb-2 rounded-lg" />
            <Skeleton className="h-4 w-full mb-2 rounded-lg" />
            <Skeleton className="h-4 w-full mb-2 rounded-lg" />
          </div>
        </div>

        {/* other */}
        <div className="flex-1">
          <div className="mt-6">
            <Skeleton className="h-4 w-20 mb-3 rounded-lg" />
            <div className="flex flex-wrap gap-2">
              <Skeleton className="h-5 w-24 rounded-xl" />
              <Skeleton className="h-5 w-24 rounded-xl" />
              <Skeleton className="h-5 w-20 rounded-xl" />
              <Skeleton className="h-5 w-24 rounded-xl" />
              <Skeleton className="h-5 w-18 rounded-xl" />
            </div>
          </div>
          <div className="mt-6">
            <div className="flex flex-col gap-2 w-full mt-4">
              <Skeleton className="h-5 w-32 rounded-lg" />
              <Skeleton className="h-5 w-full rounded-lg" />
            </div>
            <div className="flex flex-col gap-2 w-full mt-4">
              <Skeleton className="h-5 w-32 rounded-lg" />
              <Skeleton className="h-5 w-full rounded-lg" />
            </div>
            <div className="flex flex-col gap-2 w-full mt-4">
              <Skeleton className="h-5 w-32 rounded-lg" />
              <Skeleton className="h-5 w-full rounded-lg" />
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Skeleton className="h-10 w-40 rounded-full" />
      </div>

      <Skeleton className="h-16 my-10 w-full" />
    </>
  );
}
