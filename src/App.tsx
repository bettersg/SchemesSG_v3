import { LanguageProvider } from "@/i18n"
import { Navbar } from "@/components/layout/Navbar"
import { Footer } from "@/components/layout/Footer"
import { HeroSection } from "@/components/sections/HeroSection"
import { FeaturedSection } from "@/components/sections/FeaturedSection"
import { FeaturesSection } from "@/components/sections/FeaturesSection"
import { AgenciesSection } from "@/components/sections/AgenciesSection"
import { TestimonialSection } from "@/components/sections/TestimonialSection"
import { FAQSection } from "@/components/sections/FAQSection"
import { CTASection } from "@/components/sections/CTASection"

function App() {
  return (
    <LanguageProvider>
      <div className="min-h-screen bg-background text-foreground">
        <Navbar />
        <main>
          <HeroSection />
          <FeaturedSection />
          <FeaturesSection />
          <AgenciesSection />
          <TestimonialSection />
          <FAQSection />
          <CTASection />
        </main>
        <Footer />
      </div>
    </LanguageProvider>
  )
}

export default App
