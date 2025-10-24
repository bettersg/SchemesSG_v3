import { ClockIcon } from "@/assets/icons/clock-icon";
import { SearchIcon } from "@/assets/icons/search-icon";
import { StackIcon } from "@/assets/icons/stack-icon";
import { Button } from "@heroui/react";
import { useRouter } from "next/navigation";
import StatsCard from "./stats-card";
import Carousel from "./carousel";
import AboutContent from "./about-content";
import InfoCard from "./info-card";
import { DataIcon } from "@/assets/icons/data-icon";
import { CheckIcon } from "@/assets/icons/check-icon";
import { AIFileIcon } from "@/assets/icons/ai-file-icon";
import { PeopleIcon } from "@/assets/icons/people-icon";
import { ChatIcon } from "@/assets/icons/chat-icon";
import { RepeatIcon } from "@/assets/icons/repeat-icon";
import aboutusImg1 from '@/assets/about-section/about-us1.svg'
import aboutusImg2 from '@/assets/about-section/about-us2.svg'
import clsx from "clsx";

function AboutSection() {
  const router = useRouter();

  return (
    <div className="w-full">
      <section
        className={clsx(
          "flex flex-col items-center gap-6",
          "py-6 sm:py-9 md:py-12"
        )}
      >
        <div className="flex flex-col gap-4 items-center">
          <h2 className="font-bold text-xl md:text-2xl text-schemes-blue text-center">
            Built for the community, with the community
          </h2>
          <p className="text-base md:text-xl text-center">
            Making Singapore's social assistance schemes{" "}
            <span className="text-schemes-blue">easy to find</span> and{" "}
            <span className="text-schemes-blue">access</span>
          </p>
        </div>
        <div className="w-full flex flex-col sm:flex-row gap-4 justify-center items-center sm:items-stretch">
          <StatsCard title="400+" subtitle="social schemes listed">
            <StackIcon size={50} className="fill-schemes-blue" />
          </StatsCard>
          <StatsCard title="5000+" subtitle="queries since 2020">
            <SearchIcon size={50} className="fill-schemes-blue" />
          </StatsCard>
          <StatsCard title="24/7" subtitle="available">
            <ClockIcon size={50} className="fill-schemes-blue" />
          </StatsCard>
        </div>
      </section>
      <section className="flex justify-center">
        <div className={clsx("w-screen shrink-0 bg-schemes-lightblue overflow-hidden", "py-6 sm:py-9 md:py-12")}>
          <Carousel />
        </div>
      </section>
      <section
        className={clsx(
          "flex flex-col items-center gap-12",
          "py-6 sm:py-9 md:py-12"
        )}
      >
        <h2 className="text-2xl md:text-3xl font-bold text-schemes-blue text-center">
          About us
        </h2>
        <AboutContent
          title="How we started"
          subtitle="Born from the ground up"
          text="Schemes SG began as a volunteer's “help-list” for referral work. It struck a chord with social workers, volunteers and individuals in need, who needed a simpler way to cut through scattered, outdated information. That traction grew into a community effort, supported by Better.sg and shaped by real lived experiences."
          src={aboutusImg1}
          alt="A person interacts with a digital board displaying floating icons and documents, including arrows pointing to a light bulb."
        />
        <AboutContent
          title="What we're solving"
          subtitle="One central directory for all social assistance schemes"
          text="Social assistance information is often fragmented, hard to search, and slow to update. Schemes SG pulls everything into one trusted place, keeps it fresh with community input, and makes it navigable with AI-powered search and smart filters."
          src={aboutusImg2}
          alt="Illustration of a large central search bar surrounded by documents, servers, and charts, conveying digital collaboration."
          
          orderFlipped={true}
        />
      </section>
      <section
        className={clsx(
          "flex flex-col gap-4 items-center",
          "py-6 sm:py-9 md:py-12"
        )}
      >
        <h2 className="text-2xl md:text-3xl font-bold text-schemes-blue text-center">
          How it works
        </h2>
        <div className="w-full overflow-x-scroll lg:overflow-auto">
          <div
            className={clsx(
              "flex justify-start p-4",
              "lg:grid lg:grid-cols-[repeat(3,fit-content(100%))] lg:justify-center",
              "gap-4 md:gap-6"
            )}
          >
            <InfoCard
              title="Gather credible data"
              text="We gather scheme details from official websites, public sources, and community submissions."
            >
              <DataIcon className="fill-white" size={50} />
            </InfoCard>
            <InfoCard
              title="Check for accuracy"
              text="Entries are reviewed against primary documents to make sure the information you see is correct."
            >
              <CheckIcon className="fill-white" size={50} />
            </InfoCard>
            <InfoCard
              title="Enrich with AI"
              text="We use web scraping and AI to fill in missing details and make scheme descriptions more complete over time."
            >
              <AIFileIcon className="fill-white" size={50} />
            </InfoCard>
            <InfoCard
              title="Community feedback"
              text="Our users contribute new schemes and help us spot missing or outdated information fast. "
            >
              <PeopleIcon className="fill-white" size={50} />
            </InfoCard>
            <InfoCard
              title="Smart search assistant"
              text="Looking for something specific? Our chatbot helps you find relevant schemes without guesswork."
            >
              <ChatIcon className="fill-white" size={50} />
            </InfoCard>
            <InfoCard
              title="Up to date information"
              text="We run frequent refreshes to find the latest support programs and policy changes"
            >
              <RepeatIcon className="fill-white" size={50} />
            </InfoCard>
          </div>
        </div>
      </section>
      <section className={clsx("flex justify-center", "py-6 sm:py-9 md:py-12")}>
        <div className="max-w-[600px] flex flex-col items-center gap-6">
          <h2 className="text-2xl md:text-3xl font-bold text-schemes-blue text-center">
            Contact Us
          </h2>
          <p className="text-base md:text-xl text-center">
            Have a question about Schemes.sg? Get in touch with us at
            contact@schemes.sg or send us your feedback using the form below.
          </p>
          <Button
            color="primary"
            size="lg"
            onPress={() => router.push("/feedback")}
          >
            Submit your feedback
          </Button>
        </div>
      </section>
    </div>
  );
}

export default AboutSection;
