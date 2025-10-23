import AnimatedCard from "./animated-card";

function StatsCard({ title, subtitle, children }) {
  return (
    <AnimatedCard className=" rounded-md">
      <div className="flex flex-col gap-4 justify-center items-center">
        {children}
        <div className="flex flex-col gap-2 items-center text-center">
          <p className="text-2xl md:text-3xl font-semibold">{title}</p>
          <p className="text-base md:text-xl">{subtitle}</p>
        </div>
      </div>
    </AnimatedCard>
  );
}

export default StatsCard;
