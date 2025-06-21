import Link from "next/link";
import { Divider } from "@nextui-org/react";

const data = [
  {
    title: "Info",
    links: [{ label: "About", link: "/about" }],
  },
  {
    title: "Contact",
    links: [
      { label: "Feedback", link: "/feedback" },
      { label: "Contribute", link: "/contribute" },
    ],
  },
];

export default function MainFooter() {
  const groups = data.map((group) => {
    const links = group.links.map((link, idx) => {
      return (
        <Link key={idx} href={link.link} className="text-schemes-gray text-xs py-1 hover:underline">
          {link.label}
        </Link>
      );
    });

    return (
      <div className="flex flex-col w-[160px]" key={group.title}>
        <p className="text-white font-extrabold mb-[6px]">{group.title}</p>
        {links}
      </div>
    );
  });

  return (
    <footer className="bg-schemes-darkblue text-white mt-4 p-8 md:mt-8 md:px-[6rem] md:py-2 flex justify-center">
      <div className="flex justify-between">
        <div className="flex flex-wrap gap-2">{groups}</div>
      </div>
      <Divider orientation="vertical" className="divide-white" />
      <p className="text-xs">© 2025 Schemes SG.</p>
    </footer>
  );
}
