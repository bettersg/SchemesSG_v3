"use client";
import classes from "./about.module.css";
import { Chip } from "@nextui-org/react";
import { Accordion, AccordionItem } from "@nextui-org/react";

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
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="feather feather-file mr-3"
        >
          <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
          <polyline points="13 2 13 9 20 9"></polyline>
        </svg>
      ),
      content: `Schemes SG started as a side project by our product lead. A long-time
      volunteer with various VWOs, he collated a "help-list" to facilitate
      referral work and built a quick front-end to share these resources
      with his friends. The resource gained unexpected traction with social
      workers and volunteers. Sensing that a consolidated directory could
      address care workers' pain point of having to navigate the confusing
      social assistance landscape, he gathered like-minded individuals from
      friends and the better.sg tech community to improve the tool. The team
      engaged social workers, caregivers and friends to understand lived
      experiences and help-seeking practices. They found that social needs
      are often intertwined, and if technology could improve the search
      process by making sense of the entangled issues that people face, it
      would immensely alleviate mental burden faced by help-seekers and
      professionals. This inspired our natural language search tool and
      tagging system. Schemes SG is ultimately what we hope to build for the
      community, with the community. Your continued usage, feedback,
      searches and contribution of crowdsourced assistance listings help
      this tool get better everyday.`,
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
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="feather feather-unlock mr-3"
        >
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
          <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
        </svg>
      ),
      content: `Serious thought was put in before building Schemes SG. Initial
      landscape scans led to the realisation that: 1. Social assistance
      listings were piecemeal and information was fragmented across various
      sites. There were some compilations, but they were often PDF files
      hidden within the repositories of organisations' websites, so they
      might not be easy to find. Search engines might also miss them. 2.
      Even if one could get their hands on a compilation, it would take a
      million "Ctrl + F"s and painstaking excavation to find schemes, given
      how complex social assistance is. The volume of information was simply
      mind-boggling. 3. The listings might not necessarily be updated. New
      versions were usually held in completely different links. PDF listings
      also meant that social workers and volunteers had to depend on the
      original poster to issue a new version should there be changes. 4.
      There were actually intuitive directories (e.g. SupportGoWhere has
      done a great job), but they were primarily government portals and
      might not include NGO or VWO schemes. Again, the power of the
      crowdsourcing could be useful here, given the size of the non-profit
      sector. This portal hopes to address the above issues by tapping on
      the power of the crowd to make social assistance info 1) comprehensive
      and 2) updated, and then using technologies like AI/NLP and filters in
      data visualisation to make this info 3) navigable. 😊`,
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
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="feather feather-folder mr-3"
        >
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
      ),
      content: `Here are the parameters governing how the Bank was populated: 1. All
      information is public-domain. Schemes SG only agglomerates public info
      to help navigate complexity. Where individual schemes are concerned,
      we use the descriptions from the organisations' writeups wherever
      possible to let them speak for their own good work :) If we make
      edits, it is to improve search functionality, and we ensure that they
      are factually accurate. 2. Currently, Schemes SG only lists schemes
      that provide benefits in cash (financial assistance, subsidies) or in
      kind (free food, food vouchers, free clinics, special cards which
      ascribe certain benefits). We are just starting to include services
      (e.g. subsidised special education) as our team grows in capacity.
      Schemes SG does not include: 1. Auto-inclusion schemes. The purpose of
      a public aid portal is to help reduce bandwidth tax, so we see no need
      to put in extra information that social workers and volunteers have no
      scope to act on. 2. Schemes that do not have a public listing or are
      not verified. We understand that sometimes organisations may have
      reasons for keeping their assistance informal. Hence, if there is no
      public info on it, we will not include it. If the info is
      crowdsourced, we ask the contributor for a link. If there is none, we
      do our own research to populate the info.`,
    },
    {
      key: "4",
      ariaLabel: "Technical details for geeks",
      title: "Considerations behind the listings",
      startContent: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="1em"
          height="1em"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="feather feather-folder mr-3"
        >
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
      ),
      content: `Schemes Pal's natural language model involves the following transformation: 
      Bag of Words (BoW) -> TF-IDF -> latent semantic indexing (LSI). Some resources used include this, 
      this and this. We are still improving the natural language feature, and if you have engineering expertise 
      or insights to offer, reach out via the "Feedback" form.
      Our steady-state vision is that as the user base grows, we get more Schemes Bank contributions and Schemes Pal queries, 
      allowing us to train more robust and accurate semantic matches. Schemes Case, our volunteer service, 
      will cover the blind spots of the model. The three components work in tandem to create an ever-improving, 
      ever more robust Schemes SG.`,
    },
  ];

  return (
    <div className={classes.mainlayout}>
      <section className={classes.container}>
        <h1 className={classes.header}>About</h1>
        <h2 className={classes.description}>
          A little more information about how Schemes SG came to be and thinking
          behind it.
        </h2>
        <svg
          width="2560px"
          height="100px"
          preserveAspectRatio="none"
          x="0px"
          y="0px"
          viewBox="0 0 2560 100"
          class=""
        >
          <polygon points="2560 0 2560 100 0 100" fill="white"></polygon>
        </svg>
      </section>
      <div className={classes.content}>
        <Chip color="primary" className={classes.chip}>
          Our vision
        </Chip>
        <p className={classes.para}>
          Our vision is to empower social workers, volunteers, and in the long
          run self-help users, to obtain relevant information on social
          assistance in Singapore quickly, easily and accurately. We tap on the
          power of crowdsourcing to keep information comprehensive and updated,
          and leverage technology to make this information navigable.
        </p>
        <Accordion variant="splitted" className={classes.accordionItem}>
          {accordionItems.map((item) => (
            <AccordionItem
              key={item.key}
              aria-label={item.ariaLabel}
              title={item.title}
              startContent={item.startContent}
              className={classes.accordionItem}
            >
              {item.content}
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}
