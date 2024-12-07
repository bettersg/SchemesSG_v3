'use client';

import { useChat } from "@/app/providers";
import { Image, Spacer } from "@nextui-org/react";
import { useParams } from "next/navigation";
import classes from "./scheme.module.css"


export default function SchemePage() {
    const { schemes } = useChat();
    const { schemeId } = useParams();

    const getScheme = (schemeId: string) => {
        const idx = schemes.findIndex(scheme => scheme.schemeId === schemeId);
        if (idx >= 0) {
            return schemes[idx]
        } else {
            console.error("No scheme found.")
        }
    }
    // useParams returns string | string[]
    const scheme = getScheme(Array.isArray(schemeId) ? schemeId[0] : schemeId);

    return (
        scheme &&
        <div className={classes.schemeContainer}>
            <div>
                <Image
                    alt={`${scheme.agency} logo`}
                    height={60}
                    radius="sm"
                    src={scheme.image}
                    width={60}
                />
                <p className="text-2xl font-bold">{scheme.schemeName}</p>
                <p className="text-l text-default-500">{scheme.agency}</p>
            </div>
            <Spacer x={3} />
            <p className="text-base">{scheme.description}</p>

        </div>
    );
}
