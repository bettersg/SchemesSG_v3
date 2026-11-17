import type { MessageDescriptor } from "@lingui/core";
import { msg } from "@lingui/core/macro";

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
 * - Any phrase except the last must read as true one second after a send. On a
 *   healthy backend the opener is the only phrase a user ever sees, and every
 *   one of them can open — see thinkingPhraseOrder.
 * - The LAST entry is the wait-tolerant one, and order matters: it is pinned to
 *   the end so it cannot fire early. It answers "did this break?", which is not
 *   yet the user's question two seconds in.
 */
export const THINKING_PHRASES: MessageDescriptor[] = [
  msg`Reading your question`,
  msg`Getting my bearings`,
  msg`Thinking about what you need`,
  msg`Making sure I've understood you`,
  msg`Turning this over`,
  msg`Working out where to start`,
  msg`Picturing your situation`,
  msg`Thinking this through`,
  msg`Considering your options`,
  msg`Weighing what might help most`,
  msg`Looking for the right fit for you`,
  msg`Thinking about who could help`,
  msg`Piecing this together`,
  msg`Keeping your situation in mind`,
  msg`Working out what matters here`,
  msg`Sorting through the possibilities`,
  msg`Finding the best place to start`,
  msg`Checking what's out there for you`,
  msg`Giving this the thought it needs`,
  msg`Still with you`,
];

/**
 * Shuffles the whole list so any phrase can open, because the opener is usually
 * the only phrase anyone reads: the dwell floor in stream-status-steps is
 * 1800ms and a healthy backend replaces this list with a real step label sooner
 * than that, so the rotation never ticks. Pinning an opener meant every send
 * showed the same words.
 *
 * The wait-tolerant closer is held at the end — at those dwell bounds it lands
 * ~45s in, so only a genuinely slow request ever reaches it.
 */
export function thinkingPhraseOrder(
  random: () => number = Math.random,
): MessageDescriptor[] {
  const closerIndex = THINKING_PHRASES.length - 1;
  const pool = THINKING_PHRASES.slice(0, closerIndex);

  for (let i = pool.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }

  return [...pool, THINKING_PHRASES[closerIndex]];
}
