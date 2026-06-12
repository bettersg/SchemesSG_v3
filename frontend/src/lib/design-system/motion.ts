// Motion tokens. Per DESIGN.md: 150–200ms for state, 400ms for entrance, easeOut.
// All values are seconds (framer-motion's unit).
//
// Usage:
//   import { motion as m } from "@/lib/design-system/motion";
//   <motion.div transition={{ duration: m.duration.state, ease: m.ease.out }} />
//
// The animations/ folder is third-party manual installs and is NOT migrated to
// these tokens. New code, and code outside animations/, should consume these.

export const duration = {
  /** State changes: hover, focus, toggle. 150–200ms. */
  state: 0.16,
  /** Entrance: messages, cards, popovers. ~400ms. */
  entrance: 0.4,
  /** Slow entrance: hero typing, landing surfaces. */
  slow: 0.7,
} as const;

export const ease = {
  /** Default ease-out. Framer accepts strings; this is the canonical one. */
  out: "easeOut",
  /** ease-out-quart cubic-bezier, for richer entrances. */
  outQuart: [0.22, 1, 0.36, 1] as const,
  inOut: "easeInOut",
} as const;

/** Per-child stagger delay, used for sequential entrances. */
export const stagger = 0.045;

export const motion = { duration, ease, stagger };
