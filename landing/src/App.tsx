import { lazy, Suspense } from "react"
import { LanguageProvider } from "@/i18n"
import { Navbar } from "@/components/layout/Navbar"
import { Footer } from "@/components/layout/Footer"
import {
  HeroSkeleton,
  FeaturedSkeleton,
  FeaturesSkeleton,
  AgenciesSkeleton,
  TestimonialSkeleton,
  FAQSkeleton,
  CTASkeleton,
} from "@/components/shared/SectionSkeleton"

const HeroSection = lazy(() => import("@/components/sections/HeroSection").then(m => ({ default: m.HeroSection })))
const FeaturedSection = lazy(() => import("@/components/sections/FeaturedSection").then(m => ({ default: m.FeaturedSection })))
const FeaturesSection = lazy(() => import("@/components/sections/FeaturesSection").then(m => ({ default: m.FeaturesSection })))
const AgenciesSection = lazy(() => import("@/components/sections/AgenciesSection").then(m => ({ default: m.AgenciesSection })))
const TestimonialSection = lazy(() => import("@/components/sections/TestimonialSection").then(m => ({ default: m.TestimonialSection })))
const FAQSection = lazy(() => import("@/components/sections/FAQSection").then(m => ({ default: m.FAQSection })))
const CTASection = lazy(() => import("@/components/sections/CTASection").then(m => ({ default: m.CTASection })))

function App() {
  return (
    <LanguageProvider>
      <div className="min-h-screen bg-background text-foreground">
        <Navbar />
        <main>
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
        </main>
        <Footer />
      </div>
    </LanguageProvider>
  )
}

export default App
