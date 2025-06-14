"use client";
import { Chip } from "@nextui-org/chip";
import { Accordion, AccordionItem } from "@nextui-org/react";
import clsx from "clsx";

export default function AboutPage() {
  const accordionItems = [
    {
      key: "1",
      ariaLabel: "How it started",
      title: "How it started",
      startContent: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="1em"
          height="1em"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="feather feather-file mr-3"
        >
          <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
          <polyline points="13 2 13 9 20 9"></polyline>
        </svg>
      ),
      content: (
        <>
          <p className="mb-4">
            Schemes SG started as a side project by our product lead. A
            long-time volunteer with various VWOs, he collated a
            &quot;help-list&quot; to facilitate referral work and built a quick
            front-end to share these resources with his friends. The resource
            gained unexpected traction with social workers and volunteers.
            Sensing that a consolidated directory could address care
            workers&apos; pain point of having to navigate the confusing social
            assistance landscape, he gathered like-minded individuals from
            friends and the{" "}
            <a
              href="https://better.sg"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-600"
            >
              better.sg
            </a>{" "}
            community to improve the tool.
          </p>
          <p className="mb-4">
            The team engaged social workers, caregivers and friends to
            understand lived experiences and help-seeking practices. They found
            that social needs are often intertwined, and if technology could
            improve the search process by making sense of the entangled issues
            that people face, it would immensely alleviate mental burden faced
            by help-seekers and professionals. This inspired our natural
            language search tool and tagging system.
          </p>
          <p>
            Schemes SG is ultimately what we hope to build for the community,
            with the community. Your continued usage, feedback, searches and
            contribution of crowdsourced assistance listings help this tool get
            better everyday.
          </p>
        </>
      ),
    },
    {
      key: "2",
      ariaLabel: "What this platform tried to solve",
      title: "What this platform tried to solve",
      startContent: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="1em"
          height="1em"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="feather feather-unlock mr-3"
        >
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
          <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
        </svg>
      ),
      content: (
        <>
          <p>
            Serious thought was put in before building Schemes SG. Initial
            landscape scans led to the realisation that:
          </p>{" "}
          <p>
            {" "}
            1. Social assistance listings were piecemeal and information was
            fragmented across various sites. There were some compilations, but
            they were often PDF files hidden within the repositories of
            organisations&apos; websites, so they might not be easy to find.
            Search engines might also miss them.
          </p>
          <p>
            {" "}
            2. Even if one could get their hands on a compilation, it would take
            a million &quot;Ctrl + F&quot;s and painstaking excavation to find
            schemes, given how complex social assistance is. The volume of
            information was simply mind-boggling.
          </p>
          <p>
            {" "}
            3. The listings might not necessarily be updated. New versions were
            usually held in completely different links. PDF listings also meant
            that social workers and volunteers had to depend on the original
            poster to issue a new version should there be changes.{" "}
          </p>
          <p className="mb-4">
            {" "}
            This portal hopes to address the above issues by tapping on the
            power of the crowd to make social assistance info{" "}
            <strong>1) comprehensive </strong>
            and <strong>2) updated</strong>, and then using technologies like
            AI/NLP and filters in data visualisation to make this info
            <strong> 3) navigable</strong>. 😊
          </p>
        </>
      ),
    },
    {
      key: "3",
      ariaLabel: "Considerations behind the listings",
      title: "Considerations behind the listings",
      startContent: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="1em"
          height="1em"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="feather feather-folder mr-3"
        >
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
      ),
      content: (
        <>
          <p>
            <u>Here are the parameters governing how the Bank was populated:</u>
          </p>
          <p>
            {" "}
            1. All information is <strong>public-domain</strong>. Schemes SG
            only agglomerates public info to help navigate complexity. Where
            individual schemes are concerned, we use the descriptions from the
            organisations&apos; writeups wherever possible to let them speak for
            their own good work :) If we make edits, it is to improve search
            functionality, and we ensure that they are factually accurate.{" "}
          </p>
          <p className="mb-4">
            2. Currently, Schemes SG only lists schemes that{" "}
            <strong>provide benefits</strong> in cash (financial assistance,
            subsidies) or in kind (free food, food vouchers, free clinics,
            special cards which ascribe certain benefits). We are just starting
            to include services (e.g. subsidised special education) as our team
            grows in capacity.
          </p>
          <p>
            <u>Schemes SG does not include:</u>
          </p>
          <p>
            1. <strong>Auto-inclusion schemes</strong>. The purpose of a public
            aid portal is to help reduce bandwidth tax, so we see no need to put
            in extra information that social workers and volunteers have no
            scope to act on.
          </p>
          <p>
            2.{" "}
            <strong>
              Schemes that do not have a public listing or are not verified.
            </strong>
            We understand that sometimes organisations may have reasons for
            keeping their assistance informal. Hence, if there is no public info
            on it, we will not include it. If the info is crowdsourced, we ask
            the contributor for a link. If there is none, we do our own research
            to populate the info.
          </p>
        </>
      ),
    },
    {
      key: "4",
      ariaLabel: "Technical details for geeks",
      title: "Technical details for geeks",
      startContent: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="1em"
          height="1em"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="feather feather-folder mr-3"
        >
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
      ),
      content: (
        <>
          <p className="mb-4">
            We began with an existing database of schemes, enriching it through
            meticulous manual curation and leveraging web scraping techniques to
            expand our dataset. This ensured that we have a robust and
            comprehensive list of schemes complete with relevant metadata.
          </p>
          <p className="mb-4">
            We then harnessed the power of natural language processing,
            utilizing libraries like spacy and re for text preprocessing and
            lemmatization. Our choice of sentence-transformers, specifically the
            all-mpnet-base-v2 model, enabled us to generate meaningful
            embeddings that capture the essence of each scheme&apos;s intent. To
            efficiently retrieve relevant schemes, we utilized FAISS (Facebook
            AI Similarity Search) to add these embeddings to an index, allowing
            for lightning-fast searching capabilities. This indexing forms the
            backbone of our system, enabling users to find help with precision
            and speed.
          </p>
          <p className="mb-4">
            To bring the conversation to life, we utilized OpenAI gpt 4o. It
            helped us to dynamically generate conversation flows, tailoring
            interactions based on the user&apos;s emotional cues and the context
            of their inquiries.
          </p>
          <p>
            Some resources used include{" "}
            <a
              href="https://sbert.net"
              target="_blank"
              className="text-blue-500 hover:text-blue-600"
            >
              this
            </a>{" "}
            and{" "}
            <a
              href="https://www.kaggle.com/datasets/devendra45/movies-similarity"
              target="_blank"
              className="text-blue-500 hover:text-blue-600"
            >
              this
            </a>{" "}
            . We are still improving the natural language feature, and if you
            have engineering expertise or insights to offer, reach out via the{" "}
            <a
              href="https://schemes.sg/feedback"
              target="_blank"
              className="text-blue-500 hover:text-blue-600"
            >
              &quot;Feedback&quot;
            </a>{" "}
            form.
          </p>
        </>
      ),
    },
    {
      key: "5",
      ariaLabel: "Media Mentions",
      title: "Media Mentions",
      startContent: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="1em"
          height="1em"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="feather feather-folder mr-3"
        >
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
      ),
      content: (
        <>
          <p className="mb-4">We are honored to be mentioned in local media:</p>
          <p className="mb-4">
            1.{" "}
            <a
              href="https://www.channelnewsasia.com/today/big-read/social-services-technology-burnout-challenges-4847736"
              target="_blank"
              className="text-blue-500 hover:text-blue-600"
            >
              Tech is easing the workload of burnt out social workers, but the
              challenges of emotional labour remain
            </a>
          </p>
          <p>
            2.{" "}
            <a
              href="https://www.zaobao.com.sg/news/singapore/story20250112-5721639"
              target="_blank"
              className="text-blue-500 hover:text-blue-600"
            >
              公务员开发应用 助查询援助计划
            </a>
          </p>
        </>
      ),
    },
  ];

  return (
    <div className="w-full h-full overflow-x-hidden">
      <section className="w-full bg-schemes-darkblue">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <h1
            className={clsx(
              "text-3xl md:text-4xl lg:text-5xl",
              "font-semibold text-white",
              "pt-16 md:pt-24"
            )}
          >
            About
          </h1>
          <h2 className="text-base md:text-lg text-white font-light mt-4 mb-8">
            A little more information about how Schemes SG came to be and
            thinking behind it.
          </h2>
        </div>
        <svg
          width="100%"
          height="100"
          preserveAspectRatio="none"
          viewBox="0 0 2560 100"
          className="block"
        >
          <polygon points="2560 0 2560 100 0 100" fill="white"></polygon>
        </svg>
      </section>

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 mb-16">
        <Chip color="primary" className="mt-12 mb-6 font-semibold">
          Our vision
        </Chip>

        <p className="text-lg md:text-xl text-schemes-darkblue leading-relaxed mb-8 font-semibold">
          Our vision is to empower social workers, volunteers, and in the long
          run self-help users, to obtain relevant information on social
          assistance in Singapore quickly, easily and accurately. We tap on the
          power of crowdsourcing to keep information comprehensive and updated,
          and leverage technology to make this information navigable.
        </p>

        <Accordion variant="splitted" className="w-full">
          {accordionItems.map((item) => (
            <AccordionItem
              key={item.key}
              aria-label={item.ariaLabel}
              title={item.title}
              startContent={item.startContent}
              className="text-schemes-darkblue"
            >
              <div>{item.content}</div>
            </AccordionItem>
          ))}
        </Accordion>
      </main>
    </div>
  );
}
