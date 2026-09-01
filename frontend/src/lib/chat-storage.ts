import type {
  Message,
  QuickReplySuggestion,
} from "@/types/chat";
import type { Scheme } from "@/types/types";

export const CHAT_STORAGE_KEYS = {
  schemes: "schemes",
  messages: "userMessages",
  sessionId: "sessionID",
  quickReplies: "quickReplies",
} as const;

export type ChatState = {
  schemes: Scheme[];
  messages: Message[];
  sessionId: string;
  quickReplies: QuickReplySuggestion[];
};

export type SerializedChatState = {
  schemes: string | null;
  messages: string | null;
  sessionId: string | null;
  quickReplies: string | null;
};

function parseArray<T>(value: string | null): T[] {
  if (!value) return [];

  try {
    const parsed: unknown = JSON.parse(value);
    return Array.isArray(parsed) ? (parsed as T[]) : [];
  } catch {
    return [];
  }
}

function parseSessionId(value: string | null): string {
  if (!value) return "";

  try {
    const parsed: unknown = JSON.parse(value);
    return typeof parsed === "string" && parsed.length > 10 ? parsed : "";
  } catch {
    return "";
  }
}

function parseQuickReplies(value: string | null): QuickReplySuggestion[] {
  return parseArray<unknown>(value).filter(
    (reply): reply is QuickReplySuggestion =>
      typeof reply === "object" &&
      reply !== null &&
      "label" in reply &&
      typeof reply.label === "string" &&
      "value" in reply &&
      typeof reply.value === "string",
  );
}

export function deserializeChatState(
  stored: SerializedChatState,
): ChatState {
  return {
    schemes: parseArray<Scheme>(stored.schemes),
    messages: parseArray<Message>(stored.messages),
    sessionId: parseSessionId(stored.sessionId),
    quickReplies: parseQuickReplies(stored.quickReplies),
  };
}

export function serializeChatState(state: ChatState): SerializedChatState {
  return {
    schemes: JSON.stringify(state.schemes),
    messages: JSON.stringify(state.messages),
    sessionId: state.sessionId ? JSON.stringify(state.sessionId) : null,
    quickReplies:
      state.quickReplies.length > 0 ? JSON.stringify(state.quickReplies) : null,
  };
}
