import Image from "next/image";
import SASW from "@/assets/sasw.png";
import CareCorner from "@/assets/carecorner.png"
import Link from "next/link";

export default function Partners() {
    return (
        <div className="my-16">
            <p className="text-center text-base md:text-xl">Our Partners</p>
            <div className="flex justify-center items-center mt-3 gap-6">
                <Link className="basis-1/2 flex justify-center" href="https://sasw.org.sg" target="_blank" rel="noopener noreferrer">
                    <Image
                        src={SASW}
                        alt="SASW Logo"
                        height={80}
                        unoptimized
                        priority
                    />
                </Link>
                <Link className="basis-1/2 flex justify-center" href="https://www.carecorner.org.sg/" target="_blank" rel="noopener noreferrer">
                    <Image
                        src={CareCorner}
                        alt="Care Corner Logo"
                        height={80}
                        unoptimized
                        priority
                    />
                </Link>
            </div>
        </div>
    )
}
