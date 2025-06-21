import Image from "next/image";
import SASW from "@/assets/sasw.png";
import Link from "next/link";

export default function Partners() {
    return (
        <div className="my-16 w-full">
            <p className="text-center text-sm text-slate-500">Our Partners</p>
            <div className="flex justify-center mt-3 gap-3">
                <Link href="https://sasw.org.sg" target="_blank" rel="noopener noreferrer">
                    <Image
                        src={SASW}
                        alt="SASW Logo"
                        height={60}
                        unoptimized
                        priority
                    />
                </Link>
            </div>
        </div>
    )
}
