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
} from "@/components/landing/shared/section-skeleton";

const HeroSection = lazy(() =>
  import("@/components/landing/sections/hero-section").then((m) => ({
    default: m.HeroSection,
  })),
);
const FeaturedSection = lazy(() =>
  import("@/components/landing/sections/featured-section").then((m) => ({
    default: m.FeaturedSection,
  })),
);
const FeaturesSection = lazy(() =>
  import("@/components/landing/sections/features-section").then((m) => ({
    default: m.FeaturesSection,
  })),
);
const AgenciesSection = lazy(() =>
  import("@/components/landing/sections/agencies-section").then((m) => ({
    default: m.AgenciesSection,
  })),
);
const TestimonialSection = lazy(() =>
  import("@/components/landing/sections/testimonial-section").then((m) => ({
    default: m.TestimonialSection,
  })),
);
const FAQSection = lazy(() =>
  import("@/components/landing/sections/faq-section").then((m) => ({
    default: m.FAQSection,
  })),
);
const CTASection = lazy(() =>
  import("@/components/landing/sections/cta-section").then((m) => ({
    default: m.CTASection,
  })),
);

export default function AboutPageContent() {
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
