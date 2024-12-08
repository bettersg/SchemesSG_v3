'use client';

import { useChat } from "@/app/providers";
import { Chip, Divider, Image, Link, Spacer } from "@nextui-org/react";
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

    const getSchemeTypes = (schemeTypeStr: string) => {
        return schemeTypeStr.split(",");
    }

    return (
        scheme &&
        <div className={classes.schemeContainer}>
            <div>{getSchemeTypes(scheme.schemeType).map((schemeType: string) => <Chip color="primary" className={classes.schemeType}>{schemeType}</Chip>)}</div>
            <div className={classes.schemeTitle}>
                <Image
                    width={150}
                    height={150}
                    alt={`${scheme.agency} logo`}
                    radius="sm"
                    src={scheme.image}
                />
                <div>
                    <p className="text-5xl font-bold">{scheme.schemeName}</p>
                    <p className="text-xl text-default-500">{scheme.agency}</p>
                </div>
            </div>
            <Spacer y={1} />
            <p className="text-base">{scheme.description}</p>
            <Divider className="my-4" />
            <div>
                <p className="text-3xl font-bold">Target Audience</p>
                <Spacer y={3} />
                <p>{scheme.targetAudience}</p>
            </div>
            <Spacer y={6} />
            <div>
                <p className="text-3xl font-bold">Benefits</p>
                <p>{scheme.benefits}</p>
            </div>
            <Spacer y={6} />
            <div>
                <p className="text-3xl font-bold">Contact</p>
                <Link isExternal href={scheme.link}>{scheme.link}</Link>
            </div>

        </div>
    );
}
