import clsx from "clsx";

export default function AnimatedCard({ className, children }) {
  return (
    <div
      className={clsx(
        "w-full max-w-[250px] md:max-w-[300px] rounded-2xl p-1",
        "relative drop-shadow-xl overflow-hidden",
        className
      )}
    >
      <div className="h-full rounded-lg p-4 bg-white">{children}</div>
      <div
        className={clsx(
          "w-[200%] h-[200%]",
          "absolute top-1/2 -left-1/2",
          "rounded-lg -z-10 origin-top",
          "blur-sm bg-gradient-to-br from-schemes-blue via-white to-white",
          "animate-[spinner-spin_3s_linear_infinite]"
        )}
      ></div>
    </div>
  );
}
