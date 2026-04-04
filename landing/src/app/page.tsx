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
} from "@/components/shared";

const HeroSection = lazy(() =>
  import("@/components/sections/HeroSection").then((m) => ({
    default: m.HeroSection,
  }))
);
const FeaturedSection = lazy(() =>
  import("@/components/sections/FeaturedSection").then((m) => ({
    default: m.FeaturedSection,
  }))
);
const StatsAndHowItWorksSection = lazy(() =>
  import("@/components/sections/StatsAndHowItWorksSection").then((m) => ({
    default: m.StatsAndHowItWorksSection,
  }))
);
const AgenciesSection = lazy(() =>
  import("@/components/sections/AgenciesSection").then((m) => ({
    default: m.AgenciesSection,
  }))
);
const TestimonialSection = lazy(() =>
  import("@/components/sections/TestimonialSection").then((m) => ({
    default: m.TestimonialSection,
  }))
);
const CTASection = lazy(() =>
  import("@/components/sections/CTASection").then((m) => ({
    default: m.CTASection,
  }))
);
const FAQSection = lazy(() =>
  import("@/components/sections/FAQSection").then((m) => ({
    default: m.FAQSection,
  }))
);

export default function LandingPage() {
  return (
    <>
      {/* Hero */}
      <Suspense fallback={<HeroSkeleton />}>
        <HeroSection />
      </Suspense>

      {/* Featured / press logos */}
      <Suspense fallback={<FeaturedSkeleton />}>
        <FeaturedSection />
      </Suspense>

      {/* Stats + How it works */}
      <Suspense fallback={<FeaturesSkeleton />}>
        <StatsAndHowItWorksSection />
      </Suspense>

      {/* Agencies marquee */}
      <Suspense fallback={<AgenciesSkeleton />}>
        <AgenciesSection />
      </Suspense>

      {/* Testimonials */}
      <Suspense fallback={<TestimonialSkeleton />}>
        <TestimonialSection />
      </Suspense>

	  {/* CTA */}
      <Suspense fallback={<CTASkeleton />}>
        <CTASection />
      </Suspense>

      {/* FAQ */}
      <Suspense fallback={<FAQSkeleton />}>
        <FAQSection />
      </Suspense>
    </>
  );
}
