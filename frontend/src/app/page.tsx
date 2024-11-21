'use client';

import MainChat from "@/components/main-chat/main-chat";
import { Spacer } from "@nextui-org/react";
import SchemesList from "@/components/schemes/schemes-list"
import React, { useState } from 'react';
import SearchBar from "@/components/search-bar/search-bar";


export default function Home() {
    const [isSchemeListShown, setIsSchemeListShown] = useState<boolean>(false);
    return (
        <main style={{ display: "flex", justifyContent: "center" }}>
            <SearchBar />
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
