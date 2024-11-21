'use client';

import MainChat from "@/components/main-chat/main-chat";
import { Spacer } from "@nextui-org/react";
import SchemesList, { Scheme } from "@/components/schemes/schemes-list"
import React, { useState } from 'react';
import SearchBar from "@/components/search-bar/search-bar";

export default function Home() {
    const [schemesResList, setSchemeResList] = useState<Scheme[]>([]);
 // TODO pass the sessionid to MainChat
    return (
        <main style={{ display: "flex", justifyContent: "center" }}>
            {
                schemesResList.length > 0
                ? <>
                    <MainChat />
                    <Spacer x={1} />
                    <SchemesList schemes={schemesResList} />
                </>
                : <SearchBar setSchemeResList={setSchemeResList} />
            }
        </main>
    )
}
