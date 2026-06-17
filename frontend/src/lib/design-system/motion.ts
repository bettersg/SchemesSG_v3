// Motion tokens. Per DESIGN.md: 150–200ms for state, 400ms for entrance,
// easeOut, and static reduced-motion fallbacks for persistent animations.
// Durations and delays are seconds for Framer Motion unless suffixed with Ms.
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
  /** Slightly more visible state change while staying under 200ms. */
  stateEmphasis: 0.18,
  /** Entrance: messages, cards, popovers. ~400ms. */
  entrance: 0.4,
  /** Slow entrance: hero typing, landing surfaces. */
  slow: 0.7,
} as const;

export const ease = {
  /** Default ease-out. Framer accepts strings; this is the canonical one. */
  out: "easeOut",
  linear: "linear",
  /** ease-out-quart cubic-bezier, for richer entrances. */
  outQuart: [0.22, 1, 0.36, 1] as const,
  inOut: "easeInOut",
} as const;

export const delay = {
  none: 0,
  heroHeadline: 0.1,
  landingSection: 0.1,
  landingSectionTrailing: 0.2,
  heroSubtitle: 0.3,
  heroComposer: 0.45,
  testimonialStagger: 0.15,
  tooltipPreviewMs: 250,
} as const;

export const timeout = {
  followUpHoldMs: 450,
  copiedResetMs: 1500,
  shareStatusResetMs: 2000,
  schemesTabPulseMs: 2200,
  anchorSelectionLockMs: 1000,
} as const;

export const offset = {
  xs: 4,
  card: 6,
  sm: 10,
  md: 20,
  walkthrough: 24,
  hero: 30,
  exitXs: -4,
  mobileMenu: -10,
} as const;

export const scale = {
  cardInitial: 0.985,
  full: 1,
} as const;

export const transition = {
  state: { duration: duration.state, ease: ease.out },
  stateEmphasis: { duration: duration.stateEmphasis, ease: ease.out },
  entrance: { duration: duration.entrance, ease: ease.out },
  richEntrance: { duration: duration.entrance, ease: ease.outQuart },
  slowEntrance: { duration: duration.slow, ease: ease.out },
  toggleSpring: {
    type: "spring",
    bounce: 0.15,
    duration: duration.entrance,
  },
} as const;

export const motionPreset = {
  fadeInUpXs: {
    initial: { opacity: 0, y: offset.xs },
    animate: { opacity: 1, y: 0 },
  },
  fadeInUpSm: {
    initial: { opacity: 0, y: offset.sm },
    animate: { opacity: 1, y: 0 },
  },
  fadeInUpMd: {
    initial: { opacity: 0, y: offset.md },
    animate: { opacity: 1, y: 0 },
  },
  fadeInUpHero: {
    initial: { opacity: 0, y: offset.hero },
    animate: { opacity: 1, y: 0 },
  },
  fadeInUpWalkthrough: {
    initial: { opacity: 0, y: offset.walkthrough },
    animate: { opacity: 1, y: 0 },
  },
  fadeOutUpXs: {
    exit: { opacity: 0, y: offset.exitXs },
  },
  mobileMenu: {
    initial: { opacity: 0, y: offset.mobileMenu },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: offset.mobileMenu },
  },
  schemeCardEnter: {
    initial: { opacity: 0, y: offset.card, scale: scale.cardInitial },
    animate: { opacity: 1, y: 0, scale: scale.full },
  },
} as const;

export const viewport = {
  default: { once: true, margin: "-80px" },
  close: { once: true, margin: "-40px" },
  relaxed: { once: true, margin: "-60px" },
} as const;

export const cssTransition = {
  allState: "transition-all duration-200",
  borderState: "transition-[border-color] duration-200",
  chromeState: "transition-all duration-200",
  colorsState: "transition-colors duration-200",
  heightState: "transition-[height] duration-200",
  opacityState: "transition-opacity duration-200",
  disclosureState:
    "transition-[max-height,opacity,transform,padding] duration-200",
} as const;

/** Per-child stagger delay, used for sequential entrances. */
export const stagger = 0.045;

export const staggerLimit = {
  schemeCards: 8,
} as const;

export const motion = {
  cssTransition,
  delay,
  duration,
  ease,
  motionPreset,
  offset,
  scale,
  stagger,
  staggerLimit,
  timeout,
  transition,
  viewport,
};
