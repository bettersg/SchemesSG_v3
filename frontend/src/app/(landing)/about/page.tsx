<<<<<<< HEAD
"use client";

import { lazy, Suspense } from "react";
import {
  HeroSkeleton,
  FeaturedSkeleton,
  FeaturesSkeleton,
  AgenciesSkeleton,
  TestimonialSkeleton,
  FAQSkeleton,
  CTASkeleton,
} from "@/components/landing/shared/SectionSkeleton";

const HeroSection = lazy(() =>
  import("@/components/landing/sections/HeroSection").then((m) => ({
    default: m.HeroSection,
  }))
);
const FeaturedSection = lazy(() =>
  import("@/components/landing/sections/FeaturedSection").then((m) => ({
    default: m.FeaturedSection,
  }))
);
const FeaturesSection = lazy(() =>
  import("@/components/landing/sections/FeaturesSection").then((m) => ({
    default: m.FeaturesSection,
  }))
);
const AgenciesSection = lazy(() =>
  import("@/components/landing/sections/AgenciesSection").then((m) => ({
    default: m.AgenciesSection,
  }))
);
const TestimonialSection = lazy(() =>
  import("@/components/landing/sections/TestimonialSection").then((m) => ({
    default: m.TestimonialSection,
  }))
);
const FAQSection = lazy(() =>
  import("@/components/landing/sections/FAQSection").then((m) => ({
    default: m.FAQSection,
  }))
);
const CTASection = lazy(() =>
  import("@/components/landing/sections/CTASection").then((m) => ({
    default: m.CTASection,
  }))
);

export default function AboutPage() {
  return (
    <>
      <Suspense fallback={<HeroSkeleton />}>
        <HeroSection />
      </Suspense>
      <Suspense fallback={<FeaturedSkeleton />}>
        <FeaturedSection />
      </Suspense>
      <Suspense fallback={<FeaturesSkeleton />}>
        <FeaturesSection />
      </Suspense>
      <Suspense fallback={<AgenciesSkeleton />}>
        <AgenciesSection />
      </Suspense>
      <Suspense fallback={<TestimonialSkeleton />}>
        <TestimonialSection />
      </Suspense>
      <Suspense fallback={<FAQSkeleton />}>
        <FAQSection />
      </Suspense>
      <Suspense fallback={<CTASkeleton />}>
        <CTASection />
      </Suspense>
    </>
  );
}
=======
"use client";

import { lazy, Suspense } from "react";
import {
  HeroSkeleton,
  FeaturedSkeleton,
  FeaturesSkeleton,
  AgenciesSkeleton,
  TestimonialSkeleton,
  FAQSkeleton,
  CTASkeleton,
} from "@/components/landing/shared/SectionSkeleton";

const HeroSection = lazy(() =>
  import("@/components/landing/sections/HeroSection").then((m) => ({
    default: m.HeroSection,
  }))
);
const FeaturedSection = lazy(() =>
  import("@/components/landing/sections/FeaturedSection").then((m) => ({
    default: m.FeaturedSection,
  }))
);
const FeaturesSection = lazy(() =>
  import("@/components/landing/sections/FeaturesSection").then((m) => ({
    default: m.FeaturesSection,
  }))
);
const AgenciesSection = lazy(() =>
  import("@/components/landing/sections/AgenciesSection").then((m) => ({
    default: m.AgenciesSection,
  }))
);
const TestimonialSection = lazy(() =>
  import("@/components/landing/sections/TestimonialSection").then((m) => ({
    default: m.TestimonialSection,
  }))
);
const FAQSection = lazy(() =>
  import("@/components/landing/sections/FAQSection").then((m) => ({
    default: m.FAQSection,
  }))
);
const CTASection = lazy(() =>
  import("@/components/landing/sections/CTASection").then((m) => ({
    default: m.CTASection,
  }))
);

export default function AboutPage() {
  return (
    <>
      <Suspense fallback={<HeroSkeleton />}>
        <HeroSection />
      </Suspense>
      <Suspense fallback={<FeaturedSkeleton />}>
        <FeaturedSection />
      </Suspense>
      <Suspense fallback={<FeaturesSkeleton />}>
        <FeaturesSection />
      </Suspense>
      <Suspense fallback={<AgenciesSkeleton />}>
        <AgenciesSection />
      </Suspense>
      <Suspense fallback={<TestimonialSkeleton />}>
        <TestimonialSection />
      </Suspense>
      <Suspense fallback={<FAQSkeleton />}>
        <FAQSection />
      </Suspense>
      <Suspense fallback={<CTASkeleton />}>
        <CTASection />
      </Suspense>
    </>
  );
}
>>>>>>> f8cdbe2 (Removed separate landing page app, revert old about page)
