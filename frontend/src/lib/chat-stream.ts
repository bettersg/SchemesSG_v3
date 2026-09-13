import type { RawSchemeData } from "@/types/types";

export type ChatStreamEvent =
  | {
      type: "chunk";
      data: {
        chunk?: string;
        content?: string;
        text?: string;
        blockIndex?: number;
        block_index?: number;
        messageIndex?: number;
        message_index?: number;
      };
    }
  | {
      type: "text";
      data: {
        text?: string;
      };
    }
  | {
      type: "action_message";
      data: {
        message?: string;
      };
    }
  | {
      type: "status";
      data: {
        label?: string;
        phase?: string;
        sessionID?: string;
        sessionId?: string;
      };
    }
  | {
      type: "schemes_update";
      data: {
        schemes?: RawSchemeData[];
      };
    }
  | {
      type: "followups";
      data: {
        items?: Record<string, string>;
      };
    }
  | {
      type: "done";
      data?: Record<string, unknown>;
    }
  | {
      type: string;
      data?: Record<string, unknown>;
    };

type ParseSseOptions = {
  flush?: boolean;
};

function parseEvent(eventText: string): ChatStreamEvent | null {
  const dataLines = eventText
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).replace(/^ /, ""));

  if (dataLines.length === 0) return null;

  const payload = dataLines.join("\n").trim();
  if (payload === "[DONE]") return { type: "done" };
  if (!payload) return null;

  try {
    const event: unknown = JSON.parse(payload);
    if (
      typeof event === "object" &&
      event !== null &&
      "type" in event &&
      typeof event.type === "string"
    ) {
      return event as ChatStreamEvent;
    }
  } catch {
    return null;
  }

  return null;
}

export function parseSseText(
  text: string,
  { flush = false }: ParseSseOptions = {},
): { events: ChatStreamEvent[]; remainder: string } {
  const eventTexts = text.split(/\r?\n\r?\n/);
  let remainder = eventTexts.pop() ?? "";

  if (flush && remainder.trim()) {
    eventTexts.push(remainder);
    remainder = "";
  }

  return {
    events: eventTexts
      .map(parseEvent)
      .filter((event): event is ChatStreamEvent => event !== null),
    remainder,
  };
}
