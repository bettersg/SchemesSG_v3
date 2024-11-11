'use client';

import MainChat from "@/components/main-chat/main-chat";
import { Spacer } from "@nextui-org/react";
import SchemesList from "@/components/schemes/schemes-list"
import { useState } from "react";

export default function Home() {
    const [isSchemeListShown, setIsSchemeListShown] = useState<boolean>(false);

    return (
        <main>
            <MainChat setIsSchemeListShown={setIsSchemeListShown} />
            {
                isSchemeListShown
                ? <>
                    <Spacer y={6} />
                    <SchemesList />
                </>
                : null
            }
        </main>
    )
}
