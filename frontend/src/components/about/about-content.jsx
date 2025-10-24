import Image from "next/image";
import contentBg from "@/assets/about-section/lightblue-shape-bg.svg";
import clsx from "clsx";

function AboutContent({ title, subtitle, text, src, alt, orderFlipped }) {
  return (
    <div
      className={clsx(
        "max-w-[1000px] p-6",
        "flex flex-col-reverse md:flex-row",
        "gap-4 md:gap-16 justify-center items-center",
        orderFlipped && "flex-col-reverse md:flex-row-reverse"
      )}
    >
      <div className="flex flex-col gap-2">
        <h3 className="text-xl md:text-2xl font-semibold text-schemes-blue text-center md:text-left">{title}</h3>
        <h4 className="text-base md:text-xl font-semibold text-center md:text-left">{subtitle}</h4>
        <p className="max-w-[500px] text-base md:text-xl text-center md:text-left">{text}</p>
      </div>
      <div className="relative shrink-0 basis-1/3">
        <Image src={src} alt={alt} fill={true}/>
        <Image
          width={300}
          height={300}
          src={contentBg}
          alt="background image"
          role="presentation"
          aria-hidden={true}
        />
      </div>
    </div>
  );
}

export default AboutContent;
