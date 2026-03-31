
/**
 * Shared style utilities for Radix primitives
 * Tron-inspired glassmorphism design system
 */
import { glassCard } from "./glass-card.styles";

// Re-export for backward compatibility
export { glassCard };

// Base glassmorphism classes with Tron aesthetic - TRUE GLASS EFFECT
export const glassmorphism = {
  // Background variations - TRUE TRANSPARENCY for glass effect
  background: {
    subtle: "backdrop-blur-xl bg-white/5 dark:bg-white/10",
    strong: "backdrop-blur-xl bg-white/10 dark:bg-white/20",
    card: "backdrop-blur-xl bg-white/5 dark:bg-white/10",
    // Tron-style colored backgrounds - VERY transparent with strong blur
    cyan: "backdrop-blur-xl bg-cyan-400/5 dark:bg-cyan-400/10",
    blue: "backdrop-blur-xl bg-blue-400/5 dark:bg-blue-400/10",
    purple: "backdrop-blur-xl bg-purple-400/5 dark:bg-purple-400/10",
    yellow: "backdrop-blur-xl bg-yellow-400/5 dark:bg-yellow-400/10",
  },

  // Border styles for glass effect - more prominent for edge definition
  border: {
    default: "border border-white/10 dark:border-white/[0.06]",
    cyan: "border border-cyan-400/50 dark:border-cyan-400/40",
    blue: "border border-blue-400/50 dark:border-blue-400/40",
    purple: "border border-purple-400/50 dark:border-purple-400/40",
    yellow: "border border-yellow-400/50 dark:border-yellow-400/40",
    focus: "focus:border-cyan-400 focus:shadow-[0_0_30px_10px_rgba(34,211,238,0.6)]",
    hover: "hover:border-cyan-400/80 hover:shadow-[0_0_25px_5px_rgba(34,211,238,0.5)]",
  },

  // Interactive states
  interactive: {
    base: "transition-all duration-200",
    hover: "hover:bg-cyan-500/10 dark:hover:bg-cyan-400/10",
    active: "active:bg-cyan-500/20 dark:active:bg-cyan-400/20",
    selected:
      "data-[state=checked]:bg-cyan-500/20 dark:data-[state=checked]:bg-cyan-400/20 data-[state=checked]:text-cyan-700 dark:data-[state=checked]:text-cyan-300",
    disabled: "disabled:opacity-50 disabled:cursor-not-allowed",
  },

  // Animation presets
  animation: {
    fadeIn:
      "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
    slideIn: "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
    slideFromTop: "data-[side=bottom]:slide-in-from-top-2",
    slideFromBottom: "data-[side=top]:slide-in-from-bottom-2",
    slideFromLeft: "data-[side=right]:slide-in-from-left-2",
    slideFromRight: "data-[side=left]:slide-in-from-right-2",
  },

  // Shadow effects with Tron-style neon glow
  shadow: {
    sm: "shadow-sm dark:shadow-md",
    md: "shadow-md dark:shadow-lg",
    lg: "shadow-lg dark:shadow-2xl",
    elevated: "shadow-[0_10px_30px_-15px_rgba(0,0,0,0.1)] dark:shadow-[0_10px_30px_-15px_rgba(0,0,0,0.7)]",
    // Strong neon glow effects for true Tron aesthetic
    glow: {
      purple: "shadow-[0_0_30px_10px_rgba(168,85,247,0.5)] dark:shadow-[0_0_40px_15px_rgba(168,85,247,0.7)]",
      blue: "shadow-[0_0_30px_10px_rgba(59,130,246,0.5)] dark:shadow-[0_0_40px_15px_rgba(59,130,246,0.7)]",
      green: "shadow-[0_0_30px_10px_rgba(34,197,94,0.5)] dark:shadow-[0_0_40px_15px_rgba(34,197,94,0.7)]",
      red: "shadow-[0_0_30px_10px_rgba(239,68,68,0.5)] dark:shadow-[0_0_40px_15px_rgba(239,68,68,0.7)]",
      orange: "shadow-[0_0_30px_10px_rgba(251,146,60,0.5)] dark:shadow-[0_0_40px_15px_rgba(251,146,60,0.7)]",
      cyan: "shadow-[0_0_30px_10px_rgba(34,211,238,0.5)] dark:shadow-[0_0_40px_15px_rgba(34,211,238,0.7)]",
      pink: "shadow-[0_0_30px_10px_rgba(236,72,153,0.5)] dark:shadow-[0_0_40px_15px_rgba(236,72,153,0.7)]",
    },
  },

  // Edge glow positions
  edgePositions: {
    none: "",
    top: "before:content-[''] before:absolute before:top-0 before:left-0 before:right-0 before:h-[2px]",
    left: "before:content-[''] before:absolute before:top-0 before:left-0 before:bottom-0 before:w-[2px]",
    right: "before:content-[''] before:absolute before:top-0 before:right-0 before:bottom-0 before:w-[2px]",
    bottom: "before:content-[''] before:absolute before:bottom-0 before:left-0 before:right-0 before:h-[2px]",
  },

  // Configurable sizes for cards
  sizes: {
    card: {
      sm: "p-4 max-w-sm",
      md: "p-6 max-w-md",
      lg: "p-8 max-w-lg",
      xl: "p-10 max-w-xl",
    },
  },

  // Priority colors (matching our task system)
  priority: {
    critical: {
      background: "bg-red-100/80 dark:bg-red-500/20",
      text: "text-red-600 dark:text-red-400",
      hover: "hover:bg-red-200 dark:hover:bg-red-500/30",
      glow: "hover:shadow-[0_0_10px_rgba(239,68,68,0.3)]",
    },
    high: {
      background: "bg-orange-100/80 dark:bg-orange-500/20",
      text: "text-orange-600 dark:text-orange-400",
      hover: "hover:bg-orange-200 dark:hover:bg-orange-500/30",
      glow: "hover:shadow-[0_0_10px_rgba(249,115,22,0.3)]",
    },
    medium: {
      background: "bg-blue-100/80 dark:bg-blue-500/20",
      text: "text-blue-600 dark:text-blue-400",
      hover: "hover:bg-blue-200 dark:hover:bg-blue-500/30",
      glow: "hover:shadow-[0_0_10px_rgba(59,130,246,0.3)]",
    },
    low: {
      background: "bg-gray-100/80 dark:bg-gray-500/20",
      text: "text-gray-600 dark:text-gray-400",
      hover: "hover:bg-gray-200 dark:hover:bg-gray-500/30",
      glow: "hover:shadow-[0_0_10px_rgba(107,114,128,0.3)]",
    },
  },
};

// Compound styles for common patterns
export const compoundStyles = {
  interactiveElement: `
    ${glassmorphism.interactive.base}
    ${glassmorphism.interactive.hover}
    ${glassmorphism.interactive.disabled}
  `,
  floatingPanel: `
    ${glassmorphism.background.strong}
    ${glassmorphism.border.strong || glassmorphism.border.default}
    ${glassmorphism.shadow.lg}
    ${glassmorphism.animation.fadeIn}
    ${glassmorphism.animation.slideIn}
  `,
  formControl: `
    ${glassmorphism.background.subtle}
    ${glassmorphism.border.default}
    ${glassmorphism.border.hover}
    ${glassmorphism.border.focus}
    ${glassmorphism.interactive.base}
    ${glassmorphism.interactive.disabled}
  `,
  card: `
    ${glassmorphism.background.card}
    ${glassmorphism.border.default}
    ${glassmorphism.shadow.md}
  `,
};

// Utility function to combine classes
export function cn(...classes: (string | undefined | false)[]): string {
  return classes.filter(Boolean).join(" ");
}
