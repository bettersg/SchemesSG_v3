'use client';

import { useEffect, useState } from "react";
import { Chip, Divider, Image, Link, Spacer } from "@nextui-org/react";
import { useParams } from "next/navigation";
import classes from "./scheme.module.css";
import { SearchResScheme } from "@/components/schemes/schemes-list";

// Type for full scheme properties
type Scheme = SearchResScheme & {
    lastUpdated?: string;
    eligibility?: {
        criteria: string;
        requiredDocuments: string[];
    };
    application?: {
        process: string;
        deadline: string;
        formLink: string;
        termsAndConditions: string;
    };
    contact?: {
        phone: string;
        email: string;
        address: string;
        website: string;
        socialMedia?: {
            facebook?: string;
            instagram?: string;
            linkedin?: string;
        };
        feedbackLink: string;
    };
    additionalInfo?: {
        faqs?: { question: string; answer: string }[];
        successStories?: { title: string; url: string }[];
        relatedSchemes?: { id: string; scheme: string; agency: string; link: string }[];
        additionalResources?: { title: string; url: string }[];
        programmeDuration?: string;
        languageOptions?: string[];
    };
};

const mapToFullScheme = (rawData: any): Scheme => {
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

  useEffect(() => {
    async function fetchScheme() {
      if (!schemeId) return;

      try {
        const id = Array.isArray(schemeId) ? schemeId[0] : schemeId;
        const response = await fetch(
          `http://localhost:5001/schemessg-v3-dev/asia-southeast1/schemes/${id}`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch scheme");
        }
        const res = await response.json();
        const schemeRes = mapToFullScheme(res.data);
        setScheme(schemeRes);
      } catch (err: any) {
        console.error("Error fetching scheme:", err);
        setError(err.message || "An unexpected error occurred");
    }
    }

    fetchScheme();
  }, [schemeId]);

  if (error) {
    return <p className="text-error">{error}</p>;
  }

  if (!scheme) {
    return <p>Loading...</p>;
  }

  // Helper to extract scheme types
  const getSchemeTypes = (schemeTypeStr: string) => schemeTypeStr.split(",");

  return (
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

      {scheme.contact && (
        <div>
          <p className="text-3xl font-bold">Contact</p>
          <p>Phone: {scheme.contact.phone}</p>
          <p>Email: {scheme.contact.email}</p>
          <p>Website: <Link isExternal href={scheme.contact.website}>{scheme.contact.website}</Link></p>
          <p>Address: {scheme.contact.address}</p>
        </div>
      )}
    </div>
  );
}
