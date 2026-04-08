"use client";
import { useChat } from "@/providers";
import { RawSchemeData, SearchResScheme } from "@/types/types";
import { useEffect, useRef, useState } from "react";
import SchemesList from "@/components/chat/schemes-list";
import SchemesPopoverButton from "@/components/chat/schemes-popover-button";
import ChatMessageList from "@/components/chat/chat-message-list";
import ChatInputBar from "@/components/chat/chat-input-bar";
import QuickReplyChips, {
  QuickReply,
} from "@/components/chat/quick-reply-chips";
import SchemeDrawer from "@/components/schemes/scheme-drawer";
import { Button, Tabs } from "@heroui/react";
import ResetQueryModal from "@/components/reset-query-modal";
import { mapToScheme, streamChat } from "@/lib/schemes";

export default function ChatPage() {
  const { messages, setMessages, sessionId, setSchemes, setSessionId } =
    useChat();

  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [selectedSchemeId, setSelectedSchemeId] = useState<string | null>(null);
  const [quickReplies, setQuickReplies] = useState<QuickReply[]>([]);
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const streamingMessageRef = useRef("");

  const handleStreamStart = () => {
    setIsGenerating(true);
  };

  const handleStreamChunk = (text: string) => {
    const json = JSON.parse(text);
    const data = json.data;
    switch (json.type) {
      case "status":
        console.log(data.label);
        if (data.phase == "session_started") {
          setSessionId(data.sessionID);
        }
        setStatusMessage(data.label);
        break;
      case "chunk":
        const textChunk = json.data.chunk;
        setStreamingMessage((prevMsg) => prevMsg + textChunk);
        streamingMessageRef.current += textChunk;
        break;
      case "schemes_update":
        if (data.schemes && data.schemes.length > 0) {
          console.log(data.schemes);
          const parsedSchemes: SearchResScheme[] = data.schemes.map(
            (scheme: RawSchemeData) => mapToScheme(scheme),
          );
          setSchemes(parsedSchemes);
        }
        break;
      case "followups":
        console.log("followup", data);
        const quickReplies: QuickReply[] = Object.entries(data.items).map(
          ([key, value]) => {
            return {
              label: key,
              value: value as string,
            };
          },
        );
        setQuickReplies(quickReplies);
        break;
      case "done":
        break;
    }
  };

  const handleStreamError = () => {
    addBotMessage("Sorry, something went wrong. Please try again.");
    setIsGenerating(false);
  };

  const handleStreamEnd = () => {
    addBotMessage(streamingMessageRef.current);
    setIsGenerating(false);
    setStreamingMessage("");
    setStatusMessage("");
    streamingMessageRef.current = "";
  };

  const fetchResponse = async (userMessage: string, sessionId?: string) => {
    await streamChat(
      userMessage,
      {
        onStart: handleStreamStart,
        onChunk: handleStreamChunk,
        onError: handleStreamError,
        onEnd: handleStreamEnd,
      },
      sessionId,
    );
  };

  const addBotMessage = (text: string) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last?.type === "user") return [...prev, { type: "bot", text }];
      return prev;
    });
  };

  const handleSend = async (input: string) => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, { type: "user", text: input }]);
    await fetchResponse(input, sessionId);
  };

  const handleDrawerOpen = (schemeId: string) => {
    setSelectedSchemeId(schemeId);
    // window.history.replaceState(null, "", `/schemes/${schemeId}`);
  };

  const handleDrawerClose = () => {
    setSelectedSchemeId(null);
    // window.history.replaceState(null, "", "/");
  };

  // Trigger first AI response on mount
  useEffect(() => {
    if (messages.length === 1 && messages[0].type === "user") {
      fetchResponse(messages[0].text);
    }
  }, []);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, streamingMessage]);

  // Quick replies after each bot turn
  useEffect(() => {
    const last = messages[messages.length - 1];
    setShowQuickReplies(!!last && last.type === "bot");
  }, [messages]);

  const handleReset = () => {
    [
      "schemes",
      "userMessages",
      "sessionID",
      "userQuery",
      "totalCount",
      "nextCursor",
    ].forEach((k) => sessionStorage.removeItem(k));
    setSchemes([]);
    setMessages([]);
    setSessionId("");
  };

  return (
    <div className="w-full max-w-7xl h-[calc(100vh-70px)] mx-auto flex flex-col bg-[#f7f9fc] overflow-hidden">
      {/* Desktop: Split layout: Chat + SchemeList */}
      <div className="hidden md:flex flex-1 overflow-hidden ">
        {/* Chat column — position:relative so the left drawer can anchor to it */}
        <div className="basis-1 flex-1 flex flex-col overflow-hidden relative min-w-0">
          {/* Messages */}
          <ChatMessageList
            messages={messages}
            streamingMessage={streamingMessage}
            statusMessage={statusMessage}
            isGenerating={isGenerating}
            scrollableDivRef={scrollRef}
          />

          {/* Quick replies */}
          {showQuickReplies && !isGenerating && (
            <QuickReplyChips
              suggestions={quickReplies}
              onSelect={(s) => {
                setShowQuickReplies(false);
                handleSend(s);
              }}
            />
          )}

          {/* Input */}
          <ChatInputBar onSend={handleSend} isGenerating={isGenerating} />

          {/* Left-side drawer — position:absolute, anchored inside this column.
              On desktop it overlays only the chat column; on mobile it's a fixed bottom sheet. */}
          <SchemeDrawer
            schemeId={selectedSchemeId}
            onClose={handleDrawerClose}
          />
        </div>

        {/* Right scheme list — desktop only */}
        <SchemesList
          handleNewChat={() => setIsOpen(true)}
          isGenerating={isGenerating}
          selectedSchemeId={selectedSchemeId}
          onSelectScheme={(id) => handleDrawerOpen(id)}
        />
      </div>

      {/* Mobile:  Tabs layout */}
      <div className="relative md:hidden h-full">
        <Tabs className="w-full h-full flex flex-col">
          <Tabs.ListContainer className="px-4 flex gap-2 items-center">
            <Tabs.List aria-label="Options">
              <Tabs.Tab id="chat">
                Chat
                <Tabs.Indicator />
              </Tabs.Tab>
              <Tabs.Tab id="schemes">
                Schemes
                <Tabs.Indicator />
              </Tabs.Tab>
            </Tabs.List>
            <Button
            size="sm"
            variant="outline"
            className="border-[#e0eaf5] text-[#5F5E5A] text-xs shrink-0"
            onPress={() => setIsOpen(true)}
          >
            New chat
          </Button>
          </Tabs.ListContainer>
          <Tabs.Panel className="flex-1 min-h-0" id="chat">
            <div className="h-full basis-1 flex-1 flex flex-col overflow-hidden relative min-w-0">
              {/* Messages */}
              <ChatMessageList
                messages={messages}
                streamingMessage={streamingMessage}
                statusMessage={statusMessage}
                isGenerating={isGenerating}
                scrollableDivRef={scrollRef}
              />

              {/* Quick replies */}
              {showQuickReplies && !isGenerating && (
                <QuickReplyChips
                  suggestions={quickReplies}
                  onSelect={(s) => {
                    setShowQuickReplies(false);
                    handleSend(s);
                  }}
                />
              )}

              {/* Input */}
              <ChatInputBar onSend={handleSend} isGenerating={isGenerating} />
            </div>
          </Tabs.Panel>
          <Tabs.Panel className="flex-1 min-h-0" id="schemes">
            <SchemesList
              handleNewChat={() => setIsOpen(true)}
              isGenerating={isGenerating}
              selectedSchemeId={selectedSchemeId}
              onSelectScheme={(id) => handleDrawerOpen(id)}
            />
          </Tabs.Panel>
        </Tabs>
        <SchemeDrawer schemeId={selectedSchemeId} onClose={handleDrawerClose} />
      </div>

      {/* Reset modal */}
      <ResetQueryModal
        isOpen={isOpen}
        onOpenChange={setIsOpen}
        handleReset={handleReset}
      />
    </div>
  );
}
