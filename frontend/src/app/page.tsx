'use client';

import MainChat from "@/components/main-chat/main-chat";
import { Spacer } from "@nextui-org/react";
import SchemesList, { Scheme } from "@/components/schemes/schemes-list"
import React, { useState } from 'react';
import SearchBar from "@/components/search-bar/search-bar";

export default function Home() {
    const [schemesResList, setSchemeResList] = useState<Scheme[]>([]);
    const [sessionId, setSessionId] = useState<string>("");

    return (
        <main style={{ display: "flex", justifyContent: "center" }}>
            {
                schemesResList.length > 0
                ? <div style={{ display:"grid", gridTemplateColumns: "2fr 3fr", gap: "0.5rem"}}>
                    <MainChat />
                    <SchemesList schemes={schemesResList} />
                </div>
                : <SearchBar setSchemeResList={setSchemeResList} />
            }
        </main>
    )
}
