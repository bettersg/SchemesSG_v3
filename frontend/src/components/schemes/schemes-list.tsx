"use client";

import { Card, CardBody, CardHeader, Image, Spacer } from "@nextui-org/react";
import Link from "next/link";
// Type for scheme from search results
export type SearchResScheme = {
  schemeType: string;
  schemeName: string;
  targetAudience: string;
  agency: string;
  description: string;
  scrapedText: string;
  benefits: string;
  link: string;
  image: string;
  searchBooster: string;
  schemeId: string;
  query: string;
  similarity: number;
  quintile: number;
};

interface SchemesListProps {
  schemes: SearchResScheme[];
}

export default function SchemesList({ schemes }: SchemesListProps) {
  return (
    <div>
      <div>
        <p className="text-base font-semibold">Search Results</p>
        <p className="text-xs text-slate-500">
          Showing {schemes.length} schemes
        </p>
      </div>

      <Spacer y={3} />

      <div
        className="gap-2 grid grid-cols-1 sm:grid-cols-2"
        style={{
          overflowX: "hidden",
          overflowY: "auto",
          maxHeight: "85vh",
          padding: "0.5rem",
        }}
      >
        {schemes.map((scheme) => (
          <Link
            key={scheme.schemeId}
            href={`/schemes/${scheme.schemeId}`}
            className="w-full"
            target="_blank"
          >
            <Card shadow="sm" className="w-full" isHoverable>
              <CardHeader className="flex gap-3 font-semibold">
                <Image
                  alt={`${scheme.agency} logo`}
                  height={60}
                  radius="sm"
                  src={scheme.image}
                  width={60}
                />
                <div className="flex flex-col">
                  <p className="text-md">{scheme.schemeName}</p>
                  <p className="text-small text-default-500">{scheme.agency}</p>
                </div>
              </CardHeader>
              <CardBody>
                <p className="text-small">
                  {scheme.description.substring(0, 250) + "..."}
                </p>
              </CardBody>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
