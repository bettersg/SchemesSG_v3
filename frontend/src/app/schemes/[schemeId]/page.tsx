"use client";

import {
  AdditionalInfoType,
  ApplicationType,
  ContactType,
  EligibilityType,
  RawSchemeData,
} from "@/app/interfaces/schemes";
import { SearchResScheme } from "@/components/schemes/schemes-list";
import {
  Chip,
  Divider,
  Image,
  Link,
  Skeleton,
  Spacer,
} from "@nextui-org/react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

// Type for full scheme properties
type Scheme = SearchResScheme & {
  lastUpdated?: string;
  eligibility?: EligibilityType;
  application?: ApplicationType;
  contact?: ContactType;
  additionalInfo?: AdditionalInfoType;
};

interface FullSchemeData extends RawSchemeData {
  "Last Updated": string;
  Eligibility?: EligibilityType;
  Application?: ApplicationType;
  Contact?: ContactType;
  "Additional Info"?: AdditionalInfoType;
}

const mapToFullScheme = (rawData: FullSchemeData): Scheme => {
  return {
    // Properties from Scheme
    schemeType: rawData["Scheme Type"] || "",
    schemeName: rawData["Scheme"] || "",
    targetAudience: rawData["Who's it for"] || "",
    agency: rawData["Agency"] || "",
    description: rawData["Description"] || "",
    scrapedText: rawData["scraped_text"] || "",
    benefits: rawData["What it gives"] || "",
    link: rawData["Link"] || "",
    image: rawData["Image"] || "",
    searchBooster: rawData["search_booster(WL)"] || "",
    schemeId: rawData["scheme_id"] || "",
    query: rawData["query"] || "",
    similarity: rawData["Similarity"] || 0,
    quintile: rawData["Quintile"] || 0,

    // Additional properties for FullScheme
    lastUpdated: rawData["Last Updated"] || "",
    eligibility: rawData["Eligibility"] || undefined,
    application: rawData["Application"] || undefined,
    contact: rawData["Contact"] || undefined,
    additionalInfo: rawData["Additional Info"] || undefined,
  };
};

export default function SchemePage() {
  const { schemeId } = useParams();
  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchScheme() {
      if (!schemeId) {
        console.error("schemeId is undefined or missing.");
        setError("Invalid schemeId");
        setIsLoading(false);
        return;
      }
      try {
        const id = Array.isArray(schemeId) ? schemeId[0] : schemeId;
        console.log("Fetching scheme data for ID:", id);

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes/${id}`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch scheme");
        }
        const res = await response.json();
        const schemeRes = mapToFullScheme(res.data);
        setScheme(schemeRes);
      } catch (err) {
        console.error("Error fetching scheme:", err);
        setError("An error occurred");
      } finally {
        setIsLoading(false);
      }
    }

    fetchScheme();

    console.log("Scheme page mounted, ID:", schemeId);
  }, [schemeId]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <p className="text-error text-center">{error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col space-y-6 p-4 md:p-6 max-w-5xl mx-auto">
        <div>
          <Skeleton className="h-3 w-20 md:w-24 rounded-md" />
          <Spacer y={1} />
        </div>

        <div className="flex flex-col md:flex-row items-start md:items-center space-y-4 md:space-y-0 md:space-x-6">
          <Skeleton className="h-24 w-24 md:h-36 md:w-36 rounded-lg" />
          <div className="flex flex-col space-y-2 w-full md:w-auto">
            <Skeleton className="h-6 md:h-8 w-full md:w-[400px] rounded-md" />
            <Skeleton className="h-4 md:h-6 w-48 md:w-64 rounded-md" />
          </div>
        </div>

        <div className="flex flex-col space-y-3">
          <Skeleton className="h-4 md:h-5 w-full md:w-11/12 rounded-md" />
          <Skeleton className="h-4 md:h-5 w-full md:w-9/12 rounded-md" />
        </div>
      </div>
    );
  }

  return (
    scheme && (
      <div className="min-h-screen bg-background p-4 md:p-8">
        <div className="max-w-5xl mx-auto">
          {/* Scheme Type Chips */}
          <div className="flex flex-wrap gap-2 mb-6">
            {scheme.schemeType.split(",").map((type) => (
              <Chip key={type} color="primary" className="text-xs md:text-sm">
                {type.trim()}
              </Chip>
            ))}
          </div>

          {/* Title Section */}
          <div className="flex flex-col md:flex-row items-start md:items-center gap-1 md:gap-6 mb-8">
            <Image
              width={120}
              height={120}
              alt={`${scheme.agency} logo`}
              radius="sm"
              className="w-24 h-24 md:w-32 md:h-32 object-contain"
              src={scheme.image}
            />
            <div className="flex-1">
              <h1 className="text-4xl lg:text-5xl font-bold mb-2 break-words">
                {scheme.schemeName}
              </h1>
              <p className="text-md md:text-xl text-default-500">
                {scheme.agency}
              </p>
            </div>
          </div>

          {/* Description */}
          <div className="prose max-w-none mb-8">
            <p className="text-base md:text-lg">{scheme.description}</p>
          </div>

          <Divider className="my-8" />

          {/* Target Audience Section */}
          <section className="mb-8">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              Target Audience
            </h2>
            <p className="text-base md:text-lg">{scheme.targetAudience}</p>
          </section>

          {/* Benefits Section */}
          <section className="mb-8">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              What It Gives
            </h2>
            <p className="text-base md:text-lg">{scheme.benefits}</p>
          </section>

          {/* Contact Section */}
          <section className="mb-8">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">Contact</h2>
            <div className="space-y-2">
              <Link
                isExternal
                showAnchorIcon
                href={scheme.link}
                className="text-base md:text-lg break-words"
              >
                {scheme.link}
              </Link>

              {scheme.contact && (
                <div className="mt-4 space-y-2">
                  {scheme.contact.phone && (
                    <p className="text-base md:text-lg">
                      <span className="font-semibold">Phone:</span>{" "}
                      {scheme.contact.phone}
                    </p>
                  )}
                  {scheme.contact.email && (
                    <p className="text-base md:text-lg">
                      <span className="font-semibold">Email:</span>{" "}
                      {scheme.contact.email}
                    </p>
                  )}
                  {scheme.contact.address && (
                    <p className="text-base md:text-lg">
                      <span className="font-semibold">Address:</span>{" "}
                      {scheme.contact.address}
                    </p>
                  )}
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    )
  );
}
