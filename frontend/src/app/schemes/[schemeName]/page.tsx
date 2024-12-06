'use client';

import { useChat } from "@/app/providers";
import { Image, Spacer } from "@nextui-org/react";


type SchemePageParams = {
    schemeId: string
}

export default function SchemePage({ params: { schemeId } }: { params: SchemePageParams }) {
    const { schemes } = useChat();

    const getScheme = (schemeId: string) => {
        console.log(`schemes: ${schemes}`);
        console.log(`schemeId: ${schemeId}`);

        const idx = schemes.findIndex(scheme => scheme.schemeId === schemeId);
        if (idx !== -1) {
            return schemes[idx]
        } else {
            console.error("No scheme found.")
        }
    }
    const scheme = getScheme(schemeId);

    return (
        scheme &&
        <div>
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
