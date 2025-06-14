import clsx from "clsx";

export default function Footer() {
  return (
    <footer
      className={clsx(
        "max-md:hidden py-2",
        "bg-schemes-darkblue text-white",
        "flex justify-center"
      )}
    >
      <p className="text-xs">© 2025 Schemes SG.</p>
    </footer>
  );
}
