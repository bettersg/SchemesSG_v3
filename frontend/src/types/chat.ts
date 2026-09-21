export type UserMessage = {
  type: "user";
  text: string;
};

export type StatusStep = {
  id: string;
  label: string;
  message: string;
  phase?: string;
};

export type BotMessage = {
  type: "bot";
  text: string;
  schemeUpdateCount?: number;
  statusSteps?: StatusStep[];
  rating?: "up" | "down";
};

export type Message = UserMessage | BotMessage;

export type QuickReplySuggestion = {
  label: string;
  value: string;
};
