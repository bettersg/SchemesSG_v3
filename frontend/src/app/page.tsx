"use client";

import MainChat from "@/components/main-chat/main-chat";
import SchemesList from "@/components/schemes/schemes-list";
import SearchBar from "@/components/search-bar/search-bar";
import { useState } from "react";
import classes from "../components/main-layout/main-layout.module.css";
import { useChat } from "./providers";

export default function Home() {
  const { schemes } = useChat();
  const [sessionId, setSessionId] = useState<string>("");

  return (
    <main className={classes.homePage}>
      {schemes.length > 0 ? (
        <div className={classes.mainLayout}>
          <MainChat sessionId={sessionId} />
          <SchemesList schemes={schemes} />
        </div>
      ) : (
        <div>
          <div className={classes.welcomeMsg}>
            {/* Desktop*/}
            <div className="hidden md:block">
              <h1 className="text-center text-4xl font-bold">
                <span className="text-[#171347]">Welcome to Schemes</span>
                <span className="text-[#008AFF]">SG</span>
              </h1>
              <p className="text-[#171347] text-center mt-6 text-lg">
                This is an AI-supported search engine for public social
                assistance schemes in Singapore.
              </p>
            </div>

            {/* Mobile*/}
            <div className="block md:hidden">
              <h1 className="text-[32px] font-bold leading-tight">
                <div className="text-[#171347] text-center">Welcome to</div>
                <div className="flex items-center justify-center gap-2">
                  <span className="text-[#171347]">Schemes</span>
                  <span className="text-[#008AFF]">SG</span>
                </div>
              </h1>
              <p className="text-[#171347] mt-4 text-center leading-snug text-base">
                This is an AI-supported search engine for public social
                assistance schemes in Singapore.
              </p>
            </div>
          </div>
          <SearchBar setSessionId={setSessionId} />
        </div>
      )}
    </main>
  );
}
