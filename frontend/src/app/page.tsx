'use client';

import MainChat from "@/components/main-chat/main-chat";
import SchemesList from "@/components/schemes/schemes-list"
import React, { useState } from 'react';
import SearchBar from "@/components/search-bar/search-bar";
import { useChat } from "./providers";

export default function Home() {
    const { schemes } = useChat();
    const [sessionId, setSessionId] = useState<string>("");

    return (
        <main style={{ display: "flex", justifyContent: "center" }}>
            {
                schemes.length > 0
                ? <div style={{ display:"grid", gridTemplateColumns: "2fr 3fr", gap: "0.5rem"}}>
                    <MainChat sessionId={sessionId}/>
                    <SchemesList schemes={schemes} />
                </div>
                :
                <div>
                    <div style={{ width: "35rem", paddingBottom:"3rem" }}>
                        <div className="font-extrabold text-2xl" style={{ display:"flex", justifyContent: "center" }}>
                            <p style={{ color:"#171347" }}>Welcome to Schemes </p>
                            <p style={{ color:"#008AFF" }}>SG</p>
                        </div>
                        <p className="font-medium text-center" style={{ color:"#171347" }}>This is an AI-supported search engine for public social assistance schemes in Singapore.</p>
                    </div>
                    <SearchBar setSessionId={setSessionId} />
                </div>
            }
        </main>
    )
}
