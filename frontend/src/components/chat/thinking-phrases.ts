/**
 * Placeholder copy for the window between a message being sent and the agent
 * emitting its first real status step.
 *
 * Rules for anyone editing this list:
 *
 * - Never claim an action the agent may not take. "Searching schemes" is a lie
 *   when the agent answers from context without calling a tool. Every phrase
 *   here describes thinking, which is always true while a request is in flight.
 * - Never assert unverifiable progress ("Narrowing things down", "Getting
 *   closer"). The UI cannot know either is true, and a reassuring indicator
 *   that lies is worse than a silent one.
 * - No jokes. Users here are often in financial hardship, or are the social
 *   workers helping them.
 * - The tail must be wait-tolerant. Those phrases surface ~45s in, when the
 *   user's real question is "did this break?", so they acknowledge the wait
 *   rather than promising an ending.
 */
export const THINKING_PHRASES = [
  "Reading your question",
  "Getting my bearings",
  "Thinking about what you need",
  "Making sure I've understood you",
  "Turning this over",
  "Working out where to start",
  "Picturing your situation",
  "Thinking this through",
  "Considering your options",
  "Weighing what might help most",
  "Looking for the right fit for you",
  "Thinking about who could help",
  "Piecing this together",
  "Keeping your situation in mind",
  "Working out what matters here",
  "Sorting through the possibilities",
  "Finding the best place to start",
  "Checking what's out there for you",
  "Giving this the thought it needs",
  "Still with you",
] as const;

/**
 * The first phrase always leads — it is the one statement unconditionally true
 * the instant a message is sent. The rest are shuffled so a user sending
 * several messages in a row doesn't watch the same reel each time.
 */
export function thinkingPhraseOrder(
  random: () => number = Math.random,
): string[] {
  const [first, ...rest] = THINKING_PHRASES;

  for (let i = rest.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [rest[i], rest[j]] = [rest[j], rest[i]];
  }

  return [first, ...rest];
}
