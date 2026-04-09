import { useState } from "react";

export default function SchemeLogo({ agency, image }: { agency: string; image?: string }) {
	const [imageError, setImageError] = useState(false)
	if (!imageError) {
		return <img className="w-8 h-8" src={image} alt={`${agency} image`} onError={() => setImageError(true)}/>
	}
  const initials = agency.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase();
  return (
    <div className="w-8 h-8 rounded-lg bg-[#E6F1FB] border border-[#B5D4F4] flex items-center justify-center text-[10px] font-bold text-[#185FA5] shrink-0">
      {initials}
    </div>
  );
}