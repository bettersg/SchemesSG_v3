import cardBg from "@/assets/about-section/blue-shape-bg.svg";
import clsx from "clsx";
import Image from "next/image";
import AnimatedCard from "./animated-card";

function InfoCard({ title, text, children }) {
  return (
    <AnimatedCard className="shrink-0">
      <div
        className={clsx(
          "flex flex-col gap-4 items-center"
        )}
      >
        <div className="w-[150px] h-[150px] flex justify-center items-center isolate">
          {children}
          <Image
            width={150}
            className="absolute -z-10"
            src={cardBg}
            alt="background image"
            role="presentation"
            aria-hidden={true}
          />
        </div>
        <div className="flex flex-col gap-2">
          <h3 className="text-xl md:text-2xl font-semibold text-center">{title}</h3>
          <p className="text-base md:text-xl text-center">{text}</p>
        </div>
      </div>
    </AnimatedCard>
  );
}

export default InfoCard;
