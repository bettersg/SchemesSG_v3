"use client";
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
import classes from "./scheme.module.css";

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
      if (!schemeId) return;

      try {
        const id = Array.isArray(schemeId) ? schemeId[0] : schemeId;
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/${process.env.NEXT_PUBLIC_API_PROJECT}/${process.env.NEXT_PUBLIC_API_REGION}/schemes/${id}`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch scheme");
        }
        const res = await response.json();
        const schemeRes = mapToFullScheme(res.data);
        setScheme(schemeRes);
      } catch (err) {
        console.log(err);
        setError("An error occurred");
      } finally {
        setIsLoading(false);
      }
    }

    fetchScheme();
  }, [schemeId]);

  if (error) {
    return <p className="text-error">{error}</p>;
  }

  if (isLoading) {
    return (
      <div className="flex flex-col space-y-6 p-6">
        {/* Skeleton loader for scheme type */}
        <div>
          <Skeleton className="h-3 w-12 rounded-md bg-gray-300" />
          <Spacer y={1} />
        </div>

        {/* Skeleton loader for scheme title */}
        <div className="flex items-center space-x-4">
          <Skeleton className="h-36 w-36 rounded-full bg-gray-300" />
          <div className="flex flex-col space-y-2">
            <Skeleton className="h-8 w-3/5 rounded-md bg-gray-300" />
            <Skeleton className="h-6 w-2/5 rounded-md bg-gray-300" />
          </div>
        </div>

        <Spacer y={2} />

        {/* Skeleton loader for description */}
        <div className="flex flex-col space-y-3">
          <Skeleton className="h-5 w-11/12 rounded-md bg-gray-300" />
          <Skeleton className="h-5 w-9/12 rounded-md bg-gray-300" />
        </div>
        <Divider className="my-4" />

        {/* Skeleton loader for other sections */}
        <Skeleton className="h-8 w-1/2 rounded-md bg-gray-300" />
        <Spacer y={1} />
        <Skeleton className="h-5 w-3/4 rounded-md bg-gray-300" />
      </div>
    );
  }

  // Helper to extract scheme types
  const getSchemeTypes = (schemeTypeStr: string) => schemeTypeStr.split(",");

  return (
    scheme && (
      <div className={classes.schemeContainer}>
        <div>
          {getSchemeTypes(scheme.schemeType).map((type) => (
            <Chip key={type} color="primary" className={classes.schemeType}>
              {type}
            </Chip>
          ))}
        </div>

        <div className={classes.schemeTitle}>
          <Image
            width={150}
            height={150}
            alt={`${scheme.agency} logo`}
            radius="sm"
            src={scheme.image}
          />
          <div>
            <p className="text-5xl font-bold">{scheme.schemeName}</p>
            <p className="text-xl text-default-500">{scheme.agency}</p>
          </div>
        </div>

        <Spacer y={1} />

        <p className="text-base">{scheme.description}</p>
        <Divider className="my-4" />

        <div>
          <p className="text-3xl font-bold">Target Audience</p>
          <Spacer y={3} />
          <p>{scheme.targetAudience}</p>
        </div>

        <Spacer y={6} />

        {/* Benefits */}
        <div>
          <p className="text-3xl font-bold">What It Gives</p>
          <p>{scheme.benefits}</p>
        </div>

        <Spacer y={6} />

        {/* Benefits */}

        {/* To replace website with scheme.contact.website. Currently no such data. */}
        <div>
          <p className="text-3xl font-bold">Contact</p>
          <Link isExternal showAnchorIcon href={scheme.link}>
            {scheme.link}
          </Link>
        </div>

        <Spacer y={6} />

        {scheme.contact && (
          <div>
            <p className="text-3xl font-bold">Contact</p>
            <p>Phone: {scheme.contact.phone}</p>
            <p>Email: {scheme.contact.email}</p>
            {/* <p>Website: <Link isExternal href={scheme.contact.website}>{scheme.contact.website}</Link></p> */}
            <p>Address: {scheme.contact.address}</p>
          </div>
        )}
      </div>
    )
  );
}
