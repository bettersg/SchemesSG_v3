"use client";
import { useChat } from "@/providers";
import type { BotMessage, QuickReplySuggestion, StatusStep } from "@/providers";
import { RawSchemeData, Scheme } from "@/types/types";
import { useCallback, useEffect, useRef, useState } from "react";
import SchemesList from "@/components/chat/schemes-list";
import ChatMessageList from "@/components/chat/chat-message-list";
import ChatInputBar from "@/components/chat/chat-input-bar";
import { Tabs } from "@heroui/react";
import NewChatModal from "@/components/chat/new-chat-modal";
import { ChatStreamEvent, mapToScheme, streamChat } from "@/lib/schemes";
import { fetchWithAuth } from "@/lib/api";
import {
  productSegmentedIndicator,
  productSegmentedList,
  productSegmentedTab,
} from "@/lib/design-system/product-styles";
import { FollowUpSuggestions } from "@/components/chat/follow-up-suggestions";
import { SchemesPanelPulse } from "@/components/chat/schemes-panel-pulse";
import { StreamingErrorCard } from "@/components/chat/streaming-error-card";
import NewChatButton from "./new-chat-button";

const initialChatRequestKeys = new Set<string>();

export default function ChatPage() {
  const {
    messages,
    setMessages,
    sessionId,
    schemes,
    setSchemes,
    setSessionId,
    quickReplies,
    setQuickReplies,
    showQuickReplies,
    setShowQuickReplies,
    draftMessage,
    setDraftMessage,
  } = useChat();

  const [isGenerating, setIsGenerating] = useState(
    messages[messages.length - 1].type == "user",
  );
  const [statusSteps, setStatusSteps] = useState<StatusStep[]>([]);
  const statusStepsRef = useRef<StatusStep[]>([]);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [resetModalIsOpen, setResetModalIsOpen] = useState(false);
  const [streamingBlocks, setStreamingBlocks] = useState<string[]>([]);
  const streamingBlocksRef = useRef<string[]>([]);

  // tracks number of schemes found when schemes list updates
  const schemesFoundCountRef = useRef(0);

  // guard against stale requests
  const activeRequestIdRef = useRef(0);
  // controller to abort requests on error / cancel
  const abortControllerRef = useRef<AbortController | null>(null);

  // snapshots chat state before sending request
  const schemesBeforeActiveRequestRef = useRef<Scheme[]>([]);
  const quickRepliesBeforeActiveRequestRef = useRef<QuickReplySuggestion[]>([]);
  const showQuickRepliesBeforeActiveRequestRef = useRef(false);
  const lastUserMessageRef = useRef("");
  const hasVisibleQuickReplies =
    showQuickReplies && !isGenerating && quickReplies.length > 0;
  const schemesListIsLoading = isGenerating && schemes.length === 0;

  // Resume the last turn on mount when it has no answer yet. Covers both the
  // initial query from the hero and a refresh/interruption mid-stream: the user
  // message is persisted but the bot reply only commits on stream end, so a
  // reload would otherwise strand the user with a question and no response.
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.type === "user") {
      const requestKey = `${sessionId || "new"}:${messages.length}:${lastMessage.text}`;
      if (initialChatRequestKeys.has(requestKey)) return;
      initialChatRequestKeys.add(requestKey);
      fetchResponse(lastMessage.text, sessionId || undefined).finally(() => {
        initialChatRequestKeys.delete(requestKey);
      });
    }
  }, []);

  const handleSend = async (input: string) => {
    const trimmed = input.trim();
    if (!trimmed || isGenerating) return;
    setMessages((prev) => [...prev, { type: "user", text: trimmed }]);
    setDraftMessage("");
    await fetchResponse(trimmed, sessionId);
  };

  const handleStopGenerating = () => {
    abortControllerRef.current?.abort();
    rollbackActiveRequest();
  };

  // Toggle a thumbs rating on a bot message. Clicking the active rating clears
  // it (undo). State persists in sessionStorage for instant UI; we also POST
  // the rating to the backend (best-effort) so it's recorded server-side.
  const handleRate = (index: number, rating: "up" | "down") => {
    const current = messages[index];
    const nextRating =
      current?.type === "bot" && current.rating === rating ? null : rating;

    setMessages((prev) =>
      prev.map((message, i) => {
        if (i !== index || message.type !== "bot") return message;
        return { ...message, rating: nextRating ?? undefined };
      }),
    );

    if (!sessionId) return;
    void fetchWithAuth(`${process.env.NEXT_PUBLIC_API_BASE_URL}/feedback`, {
      method: "POST",
      body: JSON.stringify({
        source: "chat",
        sessionId,
        messageIndex: index,
        rating: nextRating, // null = undo
      }),
    }).catch(() => {
      // Best-effort: the rating already shows locally; ignore network failures.
    });
  };

  const fetchResponse = async (userMessage: string, sessionId?: string) => {
    // snapshots chat state
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;
    const requestId = activeRequestIdRef.current + 1;
    activeRequestIdRef.current = requestId;
    schemesBeforeActiveRequestRef.current = schemes;
    quickRepliesBeforeActiveRequestRef.current = quickReplies;
    showQuickRepliesBeforeActiveRequestRef.current = showQuickReplies;
    lastUserMessageRef.current = userMessage;
    resetStreamUi();
    setDraftMessage("");
    setQuickReplies([]);
    setShowQuickReplies(false);

    await streamChat(
      userMessage,
      {
        onStart: handleStreamStart,
        onEvent: (event) => handleStreamEvent(event, requestId),
        onError: (err) => {
          console.error(err);
          if (activeRequestIdRef.current === requestId) {
            handleStreamError();
          }
        },
        onEnd: () => {
          if (activeRequestIdRef.current === requestId) {
            handleStreamEnd();
          }
        },
      },
      sessionId,
      controller.signal,
    );
  };

  const resetStreamUi = useCallback(() => {
    streamingBlocksRef.current = [];
    schemesFoundCountRef.current = 0;
    statusStepsRef.current = [];
    setStreamingBlocks([]);
    setStatusSteps([]);
    setPendingSchemesTabPulse(false);
    setStreamError(null);
  }, []);

  const handleStreamStart = () => {
    setIsGenerating(true);
  };

  const handleStreamEvent = (event: ChatStreamEvent, requestId: number) => {
    if (activeRequestIdRef.current !== requestId) return;

    switch (event.type) {
      case "action_message": {
        const data = (event.data ?? {}) as {
          phase?: string;
          label?: string;
          message?: string;
        };
        appendStatusStep("action_message", data.label, data.message, requestId);
        break;
      }
      case "text": {
        const data = (event.data ?? {}) as {
          chunk?: string;
          content?: string;
          text?: string;
          blockIndex?: number;
          block_index?: number;
          messageIndex?: number;
          message_index?: number;
        };
        appendStreamingChunk(
          data.chunk ?? data.content ?? data.text ?? "",
          data.blockIndex ??
            data.block_index ??
            data.messageIndex ??
            data.message_index,
        );
        break;
      }
      case "status": {
        const data = (event.data ?? {}) as {
          label?: string;
          phase?: string;
          sessionID?: string;
          sessionId?: string;
        };
        if (data.phase === "session_started") {
          const nextSessionId = data.sessionID ?? data.sessionId;
          if (nextSessionId) setSessionId(nextSessionId);
        }
        break;
      }
      case "schemes_update": {
        const data = (event.data ?? {}) as { schemes?: RawSchemeData[] };
        const rawSchemes = data.schemes;
        if (rawSchemes) {
          const parsedSchemes: Scheme[] = rawSchemes.map((scheme) =>
            mapToScheme(scheme as RawSchemeData),
          );
          setSchemes(parsedSchemes);
          schemesFoundCountRef.current = parsedSchemes.length;
          setPendingSchemesTabPulse(parsedSchemes.length > 0);
        }
        break;
      }
      case "followups": {
        const data = (event.data ?? {}) as {
          items?: Record<string, string>;
        };
        const items = data.items ?? {};
        const replies = Object.entries(items).map(([key, value]) => ({
          label: key,
          value: String(value),
        }));
        setQuickReplies(replies);
        break;
      }
      case "done": {
        commitStreamingBlocks(true);
        setStatusSteps([]);
        setIsGenerating(false);
        setShowQuickReplies(true);
        break;
      }
    }
  };

  const appendStatusStep = (
    phase: string | undefined,
    label: string | undefined,
    message: string | undefined,
    requestId: number,
  ) => {
    if (!label || !message) return;
    if (streamingBlocksRef.current.some(Boolean)) return;

    const step: StatusStep = {
      id: `${requestId}-${Date.now()}-${phase ?? label}`,
      label,
      message,
      phase,
    };
    setStatusSteps((prev) => {
      if (prev.at(-1)?.label === step.label) {
        statusStepsRef.current = prev;
        return prev;
      }
      const next = [...prev, step];
      statusStepsRef.current = next;
      return next;
    });
  };

  const appendStreamingChunk = (chunk: string, blockIndex?: number) => {
    if (!chunk) return;

    setStatusSteps([]);

    const blocks = [...streamingBlocksRef.current];
    const targetIndex =
      typeof blockIndex === "number" && blockIndex >= 0
        ? blockIndex
        : Math.max(blocks.length - 1, 0);

    while (blocks.length <= targetIndex) {
      blocks.push("");
    }

    blocks[targetIndex] = `${blocks[targetIndex] ?? ""}${chunk}`;
    streamingBlocksRef.current = blocks;
    setStreamingBlocks(blocks);
  };

  const commitStreamingBlocks = useCallback(
    (includeSchemeUpdate = false) => {
      const blocks = streamingBlocksRef.current
        .map((block) => block.trim())
        .filter(Boolean);

      if (blocks.length > 0) {
        const schemeUpdateCount = includeSchemeUpdate
          ? schemesFoundCountRef.current
          : 0;
        const completedStatusSteps = includeSchemeUpdate
          ? statusStepsRef.current
          : [];
        const newBotMessages = blocks.map((text, index) => ({
          type: "bot" as const,
          text,
          ...(schemeUpdateCount > 0 && index === blocks.length - 1
            ? { schemeUpdateCount }
            : {}),
          ...(completedStatusSteps.length > 0 && index === blocks.length - 1
            ? { statusSteps: completedStatusSteps }
            : {}),
        })) as BotMessage[];
        setMessages((prev) => [...prev, ...newBotMessages]);
      }

      if (includeSchemeUpdate) {
        schemesFoundCountRef.current = 0;
        statusStepsRef.current = [];
      }
      streamingBlocksRef.current = [];
      setStreamingBlocks([]);
    },
    [setMessages],
  );

  const handleStreamError = () => {
    rollbackActiveRequest(
      "The connection dropped before the response finished. Send it again when ready.",
    );
  };

  const handleStreamEnd = () => {
    commitStreamingBlocks(true);
    setStatusSteps([]);
    setIsGenerating(false);
  };

  const rollbackActiveRequest = useCallback(
    (errorMessage?: string) => {
      activeRequestIdRef.current += 1;
      setDraftMessage(lastUserMessageRef.current);
      setMessages((prev) => {
        const next = [...prev];
        let lastUserIndex = -1;
        for (let index = next.length - 1; index >= 0; index -= 1) {
          const message = next[index];
          if (
            message.type === "user" &&
            message.text === lastUserMessageRef.current
          ) {
            lastUserIndex = index;
            break;
          }
        }
        if (lastUserIndex >= 0) {
          next.splice(lastUserIndex, 1);
        }
        return next;
      });
      setSchemes(schemesBeforeActiveRequestRef.current);
      setQuickReplies(quickRepliesBeforeActiveRequestRef.current);
      setShowQuickReplies(showQuickRepliesBeforeActiveRequestRef.current);
      streamingBlocksRef.current = [];
      setStreamingBlocks([]);
      statusStepsRef.current = [];
      setStatusSteps([]);
      setIsGenerating(false);
      schemesFoundCountRef.current = 0;
      setPendingSchemesTabPulse(false);
      setStreamError(errorMessage ?? null);
    },
    [
      setMessages,
      setSchemes,
      setQuickReplies,
      setDraftMessage,
      setShowQuickReplies,
    ],
  );

  const handleReset = () => {
    [
      "schemes",
      "userMessages",
      "sessionID",
      "userQuery",
      "totalCount",
      "nextCursor",
      "quickReplies",
    ].forEach((k) => sessionStorage.removeItem(k));
    setSchemes([]);
    setMessages([]);
    setSessionId("");
    abortControllerRef.current?.abort();
    resetStreamUi();
    setQuickReplies([]);
    setDraftMessage("");
    setIsGenerating(false);
    setShowQuickReplies(false);
  };

  // pulse schemes tab in mobile view when schemes list updated
  const [pulseSchemesTab, setPulseSchemesTab] = useState(false);
  const [pendingSchemesTabPulse, setPendingSchemesTabPulse] = useState(false);
  // pulse schemes tab in mobile view if schemes list updated
  useEffect(() => {
    if (!pendingSchemesTabPulse || schemesListIsLoading) {
      return;
    }
    setPulseSchemesTab(true);
    setPendingSchemesTabPulse(false);
  }, [pendingSchemesTabPulse, schemesListIsLoading]);
  // clear pulsing schemes tab in mobile view after 2.2s
  useEffect(() => {
    if (!pulseSchemesTab) return;
    const timeout = setTimeout(() => setPulseSchemesTab(false), 2200);
    return () => clearTimeout(timeout);
  }, [pulseSchemesTab]);

  return (
    <div className="w-full max-w-[1400px] h-full mx-auto flex flex-col bg-(--schemes-bg) overflow-hidden">
      {/* Desktop: Split layout: Chat + SchemeList */}
      <div className="hidden md:flex flex-1 overflow-hidden">
        {/* Chat column — position:relative so the left drawer can anchor to it */}
        <div className="basis-1 flex-1 flex flex-col overflow-hidden relative min-w-0">
          {/* Messages */}
          <ChatMessageList
            messages={messages}
            streamingBlocks={streamingBlocks}
            statusSteps={statusSteps}
            isGenerating={isGenerating}
            onRate={handleRate}
          />

          {/* Quick replies */}
          {hasVisibleQuickReplies && (
            <FollowUpSuggestions
              suggestions={quickReplies}
              onSelect={(s) => {
                setShowQuickReplies(false);
                handleSend(s);
              }}
            />
          )}

          {streamError && (
            <StreamingErrorCard
              message={streamError}
              onNewChat={() => setResetModalIsOpen(true)}
            />
          )}

          {/* Input */}
          <ChatInputBar
            onSend={handleSend}
            onStop={handleStopGenerating}
            isGenerating={isGenerating}
            value={draftMessage}
            onValueChange={setDraftMessage}
          />
        </div>

        {/* Right scheme list — desktop only */}
        <SchemesList
          handleNewChat={() => setResetModalIsOpen(true)}
          isGenerating={schemesListIsLoading}
        />
      </div>
      {/* Mobile:  Tabs layout */}
      <div className="relative md:hidden h-full">
        <Tabs className="w-full h-full flex flex-col gap-0!">
          <Tabs.ListContainer className="p-4 flex gap-2 items-center">
            <Tabs.List aria-label="Options" className={productSegmentedList}>
              <Tabs.Tab id="chat" className={productSegmentedTab}>
                Chat
                <Tabs.Indicator className={productSegmentedIndicator} />
              </Tabs.Tab>
              <Tabs.Tab id="schemes" className={productSegmentedTab}>
                <SchemesPanelPulse active={pulseSchemesTab}>
                  Schemes
                </SchemesPanelPulse>
                <Tabs.Indicator className={productSegmentedIndicator} />
              </Tabs.Tab>
            </Tabs.List>
            <NewChatButton onPress={() => setResetModalIsOpen(true)} />
          </Tabs.ListContainer>
          <Tabs.Panel className="flex-1 min-h-0 p-0!" id="chat">
            <div className="h-full basis-1 flex-1 flex flex-col overflow-hidden relative min-w-0">
              {/* Messages */}
              <ChatMessageList
                messages={messages}
                streamingBlocks={streamingBlocks}
                statusSteps={statusSteps}
                isGenerating={isGenerating}
                onRate={handleRate}
              />

              {/* Quick replies */}
              {hasVisibleQuickReplies && (
                <FollowUpSuggestions
                  suggestions={quickReplies}
                  onSelect={(s) => {
                    setShowQuickReplies(false);
                    handleSend(s);
                  }}
                />
              )}

              {streamError && (
                <StreamingErrorCard
                  message={streamError}
                  onNewChat={() => setResetModalIsOpen(true)}
                />
              )}

              {/* Input */}
              <ChatInputBar
                onSend={handleSend}
                onStop={handleStopGenerating}
                isGenerating={isGenerating}
                value={draftMessage}
                onValueChange={setDraftMessage}
              />
            </div>
          </Tabs.Panel>
          <Tabs.Panel className="flex-1 min-h-0 !p-0" id="schemes">
            <SchemesList
              handleNewChat={() => setResetModalIsOpen(true)}
              isGenerating={schemesListIsLoading}
            />
          </Tabs.Panel>
        </Tabs>
      </div>

      {/* Reset modal */}
      <NewChatModal
        isOpen={resetModalIsOpen}
        onOpenChange={setResetModalIsOpen}
        handleReset={handleReset}
      />
    </div>
  );
}
