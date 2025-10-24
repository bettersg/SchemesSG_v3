import cnaLogo from "@/assets/about-section/cna-logo.svg";
import hatchLogo from "@/assets/about-section/hatch-logo.svg";
import bettersgLogo from "@/assets/about-section/bettersg-logo.svg";
import lianheZhaobaoLogo from "@/assets/about-section/lianhe-zaobao-logo.svg";
import moneyfmLogo from "@/assets/about-section/moneyfm-logo.svg";
import sengkangLogo from "@/assets/about-section/sengkang-logo.svg";
import Image from "next/image";
import clsx from "clsx";

function Carousel() {
  const images = [
    { src: cnaLogo, alt: "channel news asia logo" },
    { src: lianheZhaobaoLogo, alt: "lianhe zhaobao logo" },
    { src: moneyfmLogo, alt: "money fm logo" },
    { src: bettersgLogo, alt: "better.sg logo" },
    { src: sengkangLogo, alt: "sengkang town council logo" },
    { src: hatchLogo, alt: "hatch logo" },
  ];
  return (
    <div className="flex flex-col items-center gap-6">
      <h3 className="text-xl md:text-2xl font-bold">Featured on</h3>
      <div
        className={clsx(
          "max-w-[1380px] flex justify-center overflow-hidden faded-element",
          "hover:animation-paused inline-block"
        )}
      >
        <div className="shrink-0 flex animate-slide">
          {images.map((image, index) => (
            <Image
              key={index}
              className="object-cover pointer-events-none"
              src={image.src}
              alt={image.alt}
              height={100}
            />
          ))}
        </div>
        <div className="shrink-0 flex animate-slide">
          {images.map((image, index) => (
            <Image
              key={index}
              className="object-cover pointer-events-none"
              src={image.src}
              alt={image.alt}
              height={100}
            />
          ))}
        </div>
        <div className="shrink-0 flex animate-slide">
          {images.map((image, index) => (
            <Image
              key={index}
              className="object-cover pointer-events-none"
              src={image.src}
              alt={image.alt}
              height={100}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default Carousel;
