import clsx from "clsx";

function StyledCard({ className, children }) {
  return (
    <div
      className={clsx(
        "w-full max-w-[250px] md:max-w-[300px]",
        "rounded-2xl p-4",
        "bg-schemes-lightblue/30 drop-shadow-xl", 
        "border-2 border-schemes-lightblue ",
        className
      )}
    >
      {children}
    </div>
  );
}

export default StyledCard;
