
/**
 * GlassCard specific styles for the Tron design system.
 * 
 * DESIGN NOTES (From Phase 4.6):
 * - All gradients use specific alpha values (/8, /3) to ensure true glass depth.
 * - Neon Glow effects are calculated to provide maximum vibrance without blurring text.
 * - Hover states increment alpha by ~2% for subtle interactive feedback.
 */

export const glassCard = {
  // Base glass card (true transparency) - NO blur here, controlled separately
  base: "relative rounded-lg overflow-hidden border transition-all duration-300",

  // Blur intensity levels - Visible glass effect
  // Higher blur = thicker glass appearance
  blur: {
    none: "backdrop-blur-none", // 0px
    sm: "backdrop-blur-sm", // 4px
    md: "backdrop-blur-md", // 12px
    lg: "backdrop-blur-lg", // 16px
    xl: "backdrop-blur-xl", // 24px
    "2xl": "backdrop-blur-2xl", // 40px
    "3xl": "backdrop-blur-3xl", // 64px
  },

  // Glass transparency levels - Theme-aware for better color visibility
  transparency: {
    clear: "bg-white/[0.02] dark:bg-white/[0.01]", // Maximum transparency
    light: "bg-white/[0.08] dark:bg-white/[0.05]", 
    medium: "bg-white/[0.15] dark:bg-white/[0.08]", // Balanced for reading
    frosted: "bg-white/[0.40] dark:bg-black/[0.40]", // White tint in light, black in dark
    solid: "bg-white/[0.90] dark:bg-black/[0.95]", // Near opaque
  },

  // Edge color mappings for DataCard (edge-lit cards with colored gradients)
  // Logic: solid line on edge, gradient fading into card center
  edgeColors: {
    purple: {
      solid: "bg-purple-500",
      gradient: "from-purple-500/40",
      border: "border-purple-500/30",
      bg: "bg-gradient-to-br from-purple-500/8 to-purple-600/3",
    },
    blue: {
      solid: "bg-blue-500",
      gradient: "from-blue-500/40",
      border: "border-blue-500/30",
      bg: "bg-gradient-to-br from-blue-500/8 to-blue-600/3",
    },
    cyan: {
      solid: "bg-cyan-500",
      gradient: "from-cyan-500/40",
      border: "border-cyan-500/30",
      bg: "bg-gradient-to-br from-cyan-500/8 to-cyan-600/3",
    },
    green: {
      solid: "bg-green-500",
      gradient: "from-green-500/40",
      border: "border-green-500/30",
      bg: "bg-gradient-to-br from-green-500/8 to-green-600/3",
    },
    orange: {
      solid: "bg-orange-500",
      gradient: "from-orange-500/40",
      border: "border-orange-500/30",
      bg: "bg-gradient-to-br from-orange-500/8 to-orange-600/3",
    },
    pink: {
      solid: "bg-pink-500",
      gradient: "from-pink-500/40",
      border: "border-pink-500/30",
      bg: "bg-gradient-to-br from-pink-500/8 to-pink-600/3",
    },
    red: {
      solid: "bg-red-500",
      gradient: "from-red-500/40",
      border: "border-red-500/30",
      bg: "bg-gradient-to-br from-red-500/8 to-red-600/3",
    },
  },

  // Colored glass tints - BRIGHT NEON COLORS with higher opacity for depth
  tints: {
    none: "",
    purple: {
      clear: "bg-purple-500/[0.03] dark:bg-purple-400/[0.04]", // 3-4% subtle
      light: "bg-purple-500/[0.08] dark:bg-purple-400/[0.10]", 
      medium: "bg-purple-500/[0.15] dark:bg-purple-400/[0.20]", 
      frosted: "bg-purple-500/[0.25] dark:bg-purple-400/[0.35]", 
      solid: "bg-purple-500/[0.40] dark:bg-purple-400/[0.60]", // Neon glow core
    },
    blue: {
      clear: "bg-blue-500/[0.03] dark:bg-blue-400/[0.04]",
      light: "bg-blue-500/[0.08] dark:bg-blue-400/[0.10]",
      medium: "bg-blue-500/[0.15] dark:bg-blue-400/[0.20]",
      frosted: "bg-blue-500/[0.25] dark:bg-blue-400/[0.35]",
      solid: "bg-blue-500/[0.40] dark:bg-blue-400/[0.60]",
    },
    cyan: {
      clear: "bg-cyan-500/[0.03] dark:bg-cyan-400/[0.04]",
      light: "bg-cyan-500/[0.08] dark:bg-cyan-400/[0.10]",
      medium: "bg-cyan-500/[0.15] dark:bg-cyan-400/[0.20]",
      frosted: "bg-cyan-500/[0.25] dark:bg-cyan-400/[0.35]",
      solid: "bg-cyan-500/[0.40] dark:bg-cyan-400/[0.60]",
    },
    green: {
      clear: "bg-green-500/[0.03] dark:bg-green-400/[0.04]",
      light: "bg-green-500/[0.08] dark:bg-green-400/[0.10]",
      medium: "bg-green-500/[0.15] dark:bg-green-400/[0.20]",
      frosted: "bg-green-500/[0.25] dark:bg-green-400/[0.35]",
      solid: "bg-green-500/[0.40] dark:bg-green-400/[0.60]",
    },
    orange: {
      clear: "bg-orange-500/[0.03] dark:bg-orange-400/[0.04]",
      light: "bg-orange-500/[0.08] dark:bg-orange-400/[0.10]",
      medium: "bg-orange-500/[0.15] dark:bg-orange-400/[0.20]",
      frosted: "bg-orange-500/[0.25] dark:bg-orange-400/[0.35]",
      solid: "bg-orange-500/[0.40] dark:bg-orange-400/[0.60]",
    },
    pink: {
      clear: "bg-pink-500/[0.03] dark:bg-pink-400/[0.04]",
      light: "bg-pink-500/[0.08] dark:bg-pink-400/[0.10]",
      medium: "bg-pink-500/[0.15] dark:bg-pink-400/[0.20]",
      frosted: "bg-pink-500/[0.25] dark:bg-pink-400/[0.35]",
      solid: "bg-pink-500/[0.40] dark:bg-pink-400/[0.60]",
    },
    red: {
      clear: "bg-red-500/[0.03] dark:bg-red-400/[0.04]",
      light: "bg-red-500/[0.08] dark:bg-red-400/[0.10]",
      medium: "bg-red-500/[0.15] dark:bg-red-400/[0.20]",
      frosted: "bg-red-500/[0.25] dark:bg-red-400/[0.35]",
      solid: "bg-red-500/[0.40] dark:bg-red-400/[0.60]",
    },
  },

  // Neon glow effects - BRIGHTER & MORE INTENSE (Static classes for Performance)
  variants: {
    none: {
      border: "border-gray-300/20 dark:border-white/10",
      glow: "",
      hover: "hover:bg-white/[0.04] dark:hover:bg-white/[0.02]",
    },
    purple: {
      border: "border-purple-500/50 dark:border-purple-400/40",
      glow: "shadow-[0_0_40px_15px_rgba(168,85,247,0.4)] dark:shadow-[0_0_60px_25px_rgba(168,85,247,0.7)]",
      hover: "hover:shadow-[0_0_50px_20px_rgba(168,85,247,0.5)] dark:hover:shadow-[0_0_80px_30px_rgba(168,85,247,0.8)]",
    },
    blue: {
      border: "border-blue-500/50 dark:border-blue-400/40",
      glow: "shadow-[0_0_40px_15px_rgba(59,130,246,0.4)] dark:shadow-[0_0_60px_25px_rgba(59,130,246,0.7)]",
      hover: "hover:shadow-[0_0_50px_20px_rgba(59,130,246,0.5)] dark:hover:shadow-[0_0_80px_30px_rgba(59,130,246,0.8)]",
    },
    green: {
      border: "border-green-500/50 dark:border-green-400/40",
      glow: "shadow-[0_0_40px_15px_rgba(34,197,94,0.4)] dark:shadow-[0_0_60px_25px_rgba(34,197,94,0.7)]",
      hover: "hover:shadow-[0_0_50px_20px_rgba(34,197,94,0.5)] dark:hover:shadow-[0_0_80px_30px_rgba(34,197,94,0.8)]",
    },
    cyan: {
      border: "border-cyan-500/50 dark:border-cyan-400/40",
      glow: "shadow-[0_0_40px_15px_rgba(34,211,238,0.4)] dark:shadow-[0_0_60px_25px_rgba(34,211,238,0.7)]",
      hover: "hover:shadow-[0_0_50px_20px_rgba(34,211,238,0.5)] dark:hover:shadow-[0_0_80px_30px_rgba(34,211,238,0.8)]",
    },
    orange: {
      border: "border-orange-500/50 dark:border-orange-400/40",
      glow: "shadow-[0_0_40px_15px_rgba(251,146,60,0.4)] dark:shadow-[0_0_60px_25px_rgba(251,146,60,0.7)]",
      hover: "hover:shadow-[0_0_50px_20px_rgba(251,146,60,0.5)] dark:hover:shadow-[0_0_80px_30px_rgba(251,146,60,0.8)]",
    },
    pink: {
      border: "border-pink-500/50 dark:border-pink-400/40",
      glow: "shadow-[0_0_40px_15px_rgba(236,72,153,0.4)] dark:shadow-[0_0_60px_25px_rgba(236,72,153,0.7)]",
      hover: "hover:shadow-[0_0_50px_20px_rgba(236,72,153,0.5)] dark:hover:shadow-[0_0_80px_30px_rgba(236,72,153,0.8)]",
    },
    red: {
      border: "border-red-500/50 dark:border-red-400/40",
      glow: "shadow-[0_0_40px_15px_rgba(239,68,68,0.4)] dark:shadow-[0_0_60px_25px_rgba(239,68,68,0.7)]",
      hover: "hover:shadow-[0_0_50px_20px_rgba(239,68,68,0.5)] dark:hover:shadow-[0_0_80px_30px_rgba(239,68,68,0.8)]",
    },
  },

  // Outer glow size variants (Physical logic: larger shadow spread)
  outerGlowSizes: {
    cyan: {
      sm: "shadow-[0_0_20px_rgba(34,211,238,0.3)]",
      md: "shadow-[0_0_40px_rgba(34,211,238,0.4)]",
      lg: "shadow-[0_0_70px_rgba(34,211,238,0.5)]",
      xl: "shadow-[0_0_100px_rgba(34,211,238,0.6)]",
    },
    purple: {
      sm: "shadow-[0_0_20px_rgba(168,85,247,0.3)]",
      md: "shadow-[0_0_40px_rgba(168,85,247,0.4)]",
      lg: "shadow-[0_0_70px_rgba(168,85,247,0.5)]",
      xl: "shadow-[0_0_100px_rgba(168,85,247,0.6)]",
    },
    blue: {
      sm: "shadow-[0_0_20px_rgba(59,130,246,0.3)]",
      md: "shadow-[0_0_40px_rgba(59,130,246,0.4)]",
      lg: "shadow-[0_0_70px_rgba(59,130,246,0.5)]",
      xl: "shadow-[0_0_100px_rgba(59,130,246,0.6)]",
    },
    pink: {
      sm: "shadow-[0_0_20px_rgba(236,72,153,0.3)]",
      md: "shadow-[0_0_40px_rgba(236,72,153,0.4)]",
      lg: "shadow-[0_0_70px_rgba(236,72,153,0.5)]",
      xl: "shadow-[0_0_100px_rgba(236,72,153,0.6)]",
    },
    green: {
      sm: "shadow-[0_0_20px_rgba(34,197,94,0.3)]",
      md: "shadow-[0_0_40px_rgba(34,197,94,0.4)]",
      lg: "shadow-[0_0_70px_rgba(34,197,94,0.5)]",
      xl: "shadow-[0_0_100px_rgba(34,197,94,0.6)]",
    },
    orange: {
      sm: "shadow-[0_0_20px_rgba(251,146,60,0.3)]",
      md: "shadow-[0_0_40px_rgba(251,146,60,0.4)]",
      lg: "shadow-[0_0_70px_rgba(251,146,60,0.5)]",
      xl: "shadow-[0_0_100px_rgba(251,146,60,0.6)]",
    },
    red: {
      sm: "shadow-[0_0_20px_rgba(239,68,68,0.3)]",
      md: "shadow-[0_0_40px_rgba(239,68,68,0.4)]",
      lg: "shadow-[0_0_70px_rgba(239,68,68,0.5)]",
      xl: "shadow-[0_0_100px_rgba(239,68,68,0.6)]",
    },
  },

  // Inner glow variants (inset shadows for internal depth)
  innerGlowSizes: {
    cyan: {
      sm: "shadow-[inset_0_0_15px_rgba(34,211,238,0.2)]",
      md: "shadow-[inset_0_0_40px_rgba(34,211,238,0.3)]",
      lg: "shadow-[inset_0_0_80px_rgba(34,211,238,0.4)]",
      xl: "shadow-[inset_0_0_120px_rgba(34,211,238,0.5)]",
    },
    purple: {
      sm: "shadow-[inset_0_0_15px_rgba(168,85,247,0.2)]",
      md: "shadow-[inset_0_0_40px_rgba(168,85,247,0.3)]",
      lg: "shadow-[inset_0_0_80px_rgba(168,85,247,0.4)]",
      xl: "shadow-[inset_0_0_120px_rgba(168,85,247,0.5)]",
    },
    blue: {
      sm: "shadow-[inset_0_0_15px_rgba(59,130,246,0.2)]",
      md: "shadow-[inset_0_0_40px_rgba(59,130,246,0.3)]",
      lg: "shadow-[inset_0_0_80px_rgba(59,130,246,0.4)]",
      xl: "shadow-[inset_0_0_120px_rgba(59,130,246,0.5)]",
    },
    pink: {
      sm: "shadow-[inset_0_0_15px_rgba(236,72,153,0.2)]",
      md: "shadow-[inset_0_0_40px_rgba(236,72,153,0.3)]",
      lg: "shadow-[inset_0_0_80px_rgba(236,72,153,0.4)]",
      xl: "shadow-[inset_0_0_120px_rgba(236,72,153,0.5)]",
    },
    green: {
      sm: "shadow-[inset_0_0_15px_rgba(34,197,94,0.2)]",
      md: "shadow-[inset_0_0_40px_rgba(34,197,94,0.3)]",
      lg: "shadow-[inset_0_0_80px_rgba(34,197,94,0.4)]",
      xl: "shadow-[inset_0_0_120px_rgba(34,197,94,0.5)]",
    },
    orange: {
      sm: "shadow-[inset_0_0_15px_rgba(251,146,60,0.2)]",
      md: "shadow-[inset_0_0_40px_rgba(251,146,60,0.3)]",
      lg: "shadow-[inset_0_0_80px_rgba(251,146,60,0.4)]",
      xl: "shadow-[inset_0_0_120px_rgba(251,146,60,0.5)]",
    },
    red: {
      sm: "shadow-[inset_0_0_15px_rgba(239,68,68,0.2)]",
      md: "shadow-[inset_0_0_40px_rgba(239,68,68,0.3)]",
      lg: "shadow-[inset_0_0_80px_rgba(239,68,68,0.4)]",
      xl: "shadow-[inset_0_0_120px_rgba(239,68,68,0.5)]",
    },
  },

  // Size variants for standard padding
  sizes: {
    none: "p-0",
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
    xl: "p-10",
  },

  // Edge-lit effects for cards (top, left, right, bottom edges)
  edgeLit: {
    position: {
      none: "",
      top: "before:content-[''] before:absolute before:top-0 before:left-0 before:right-0 before:h-[2px] before:rounded-t-lg",
      left: "before:content-[''] before:absolute before:top-0 before:left-0 before:bottom-0 before:w-[2px] before:rounded-l-lg",
      right:
        "before:content-[''] before:absolute before:top-0 before:right-0 before:bottom-0 before:w-[2px] before:rounded-r-lg",
      bottom:
        "before:content-[''] before:absolute before:bottom-0 before:left-0 before:right-0 before:h-[2px] before:rounded-b-lg",
    },
    color: {
      purple: {
        line: "before:bg-purple-500 dark:before:bg-purple-400",
        glow: "before:shadow-[0_0_15px_4px_rgba(168,85,247,0.8)]",
        gradient: {
          horizontal:
            "before:bg-gradient-to-r before:from-transparent before:via-purple-500 dark:before:via-purple-400 before:to-transparent",
          vertical:
            "before:bg-gradient-to-b before:from-transparent before:via-purple-500 dark:before:via-purple-400 before:to-transparent",
        },
      },
      blue: {
        line: "before:bg-blue-500 dark:before:bg-blue-400",
        glow: "before:shadow-[0_0_15px_4px_rgba(59,130,246,0.8)]",
        gradient: {
          horizontal:
            "before:bg-gradient-to-r before:from-transparent before:via-blue-500 dark:before:via-blue-400 before:to-transparent",
          vertical:
            "before:bg-gradient-to-b before:from-transparent before:via-blue-500 dark:before:via-blue-400 before:to-transparent",
        },
      },
      cyan: {
        line: "before:bg-cyan-500 dark:before:bg-cyan-400",
        glow: "before:shadow-[0_0_15px_4px_rgba(34,211,238,0.8)]",
        gradient: {
          horizontal:
            "before:bg-gradient-to-r before:from-transparent before:via-cyan-500 dark:before:via-cyan-400 before:to-transparent",
          vertical:
            "before:bg-gradient-to-b before:from-transparent before:via-cyan-500 dark:before:via-cyan-400 before:to-transparent",
        },
      },
      green: {
        line: "before:bg-green-500 dark:before:bg-green-400",
        glow: "before:shadow-[0_0_15px_4px_rgba(34,197,94,0.8)]",
        gradient: {
          horizontal:
            "before:bg-gradient-to-r before:from-transparent before:via-green-500 dark:before:via-green-400 before:to-transparent",
          vertical:
            "before:bg-gradient-to-b before:from-transparent before:via-green-500 dark:before:via-green-400 before:to-transparent",
        },
      },
      orange: {
        line: "before:bg-orange-500 dark:before:bg-orange-400",
        glow: "before:shadow-[0_0_15px_4px_rgba(251,146,60,0.8)]",
        gradient: {
          horizontal:
            "before:bg-gradient-to-r before:from-transparent before:via-orange-500 dark:before:via-orange-400 before:to-transparent",
          vertical:
            "before:bg-gradient-to-b before:from-transparent before:via-orange-500 dark:before:via-orange-400 before:to-transparent",
        },
      },
      pink: {
        line: "before:bg-pink-500 dark:before:bg-pink-400",
        glow: "before:shadow-[0_0_15px_4px_rgba(236,72,153,0.8)]",
        gradient: {
          horizontal:
            "before:bg-gradient-to-r before:from-transparent before:via-pink-500 dark:before:via-pink-400 before:to-transparent",
          vertical:
            "before:bg-gradient-to-b before:from-transparent before:via-pink-500 dark:before:via-pink-400 before:to-transparent",
        },
      },
      red: {
        line: "before:bg-red-500 dark:before:bg-red-400",
        glow: "before:shadow-[0_0_15px_4px_rgba(239,68,68,0.8)]",
        gradient: {
          horizontal:
            "before:bg-gradient-to-r before:from-transparent before:via-red-500 dark:before:via-red-400 before:to-transparent",
          vertical:
            "before:bg-gradient-to-b before:from-transparent before:via-red-500 dark:before:via-red-400 before:to-transparent",
        },
      },
    },
  },
};
