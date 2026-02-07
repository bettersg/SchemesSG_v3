import { Navbar } from "@/components/layout/Navbar"
import { Footer } from "@/components/layout/Footer"
import { HeroSection } from "@/components/sections/HeroSection"
import { TestimonialSection } from "@/components/sections/TestimonialSection"
import { FeaturesSection } from "@/components/sections/FeaturesSection"
import { AgenciesSection } from "@/components/sections/AgenciesSection"
import { FAQSection } from "@/components/sections/FAQSection"
import { CTASection } from "@/components/sections/CTASection"

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <main>
        <HeroSection />
        <TestimonialSection />
        <FeaturesSection />
        <AgenciesSection />
        <FAQSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}

export default App
