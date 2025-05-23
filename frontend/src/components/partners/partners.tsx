import Image from "next/image";
import SASW from "@/assets/images/sasw.png";

export default function Partners() {
    return (
        <div className="mt-16 w-full">
            <p className="text-center text-sm text-slate-500">Our Partners</p>
            <div className="flex justify-center mt-3 gap-3">
                <Image
                    src={SASW}
                    alt="SASW Logo"
                    height={60}
                />
            </div>
        </div>
    )
}
