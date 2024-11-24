'use client';

import MainChat from "@/components/main-chat/main-chat";
import SchemesList, { Scheme } from "@/components/schemes/schemes-list"
import React, { useEffect, useState } from 'react';
import SearchBar from "@/components/search-bar/search-bar";

export default function Home() {
    const [schemesResList, setSchemeResList] = useState<Scheme[]>([]);
    const [sessionId, setSessionId] = useState<string>("");

    return (
        <main style={{ display: "flex", justifyContent: "center" }}>
            {
                schemesResList.length > 0
                ? <div style={{ display:"grid", gridTemplateColumns: "2fr 3fr", gap: "0.5rem"}}>
                    <MainChat sessionId={sessionId}/>
                    <SchemesList schemes={schemesResList} />
                </div>
                :
                <div style={{ width: "35rem" }}>
                    <div style={{ width: "35rem", paddingBottom:"3rem" }}>
                        <div className="font-extrabold text-2xl" style={{ display:"flex", justifyContent: "center" }}>
                            <p style={{ color:"#171347" }}>Welcome to Schemes </p>
                            <p style={{ color:"#008AFF" }}>SG</p>
                        </div>
                        <p className="font-medium text-center" style={{ color:"#171347" }}>This is an AI-supported search engine for public social assistance schemes in Singapore.</p>
                    </div>
                    <SearchBar setSchemeResList={setSchemeResList} setSessionId={setSessionId} />
                </div>
            }
        </main>
    )
}
