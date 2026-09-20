"use client";

import { forwardRef, type HTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { useReducedTransparency, useHighContrast } from "@/lib/motion";

/**
 * Apple Design: Materials & depth — translucency conveys hierarchy
 * Build nav/toolbars/sheets as translucent layers with content scrolling underneath
 * Material weight encodes hierarchy: darker/heavier for structure, lighter for interactive
 * Never stack light translucent on light translucent
 */

/**
 * Base translucent material surface
 * Bigger surfaces read as thicker (stronger blur + deeper shadow)
 */
interface MaterialProps extends HTMLAttributes<HTMLDivElement> {
  /** Material weight - "light" | "regular" | "heavy" | "ultra" */
  weight?: "light" | "regular" | "heavy" | "ultra";
  /** Whether content scrolls underneath */
  elevated?: boolean;
  /** Tint color for the material */
  tint?: "none" | "white" | "dark";
  /** Custom blur override */
  blur?: "sm" | "md" | "lg" | "xl";
}

type MaterialWeight = "light" | "regular" | "heavy" | "ultra";

const MATERIAL_STYLES: Record<MaterialWeight, { blur: string; bg: string; border: string; shadow: string }> = {
  light: {
    blur: "backdrop-blur-[12px]",
    bg: "bg-white/70",
    border: "border-white/40",
    shadow: "shadow-[0_1px_2px_rgba(0,0,0,0.04)]",
  },
  regular: {
    blur: "backdrop-blur-[20px]",
    bg: "bg-white/80",
    border: "border-white/50",
    shadow: "shadow-[0_1px_3px_rgba(0,0,0,0.05),0_8px_24px_rgba(0,0,0,0.05)]",
  },
  heavy: {
    blur: "backdrop-blur-[30px]",
    bg: "bg-white/90",
    border: "border-white/60",
    shadow: "shadow-[0_2px_6px_rgba(0,0,0,0.06),0_12px_32px_rgba(0,0,0,0.06)]",
  },
  ultra: {
    blur: "backdrop-blur-[40px]",
    bg: "bg-white/95",
    border: "border-white/70",
    shadow: "shadow-[0_4px_12px_rgba(0,0,0,0.08),0_20px_48px_rgba(0,0,0,0.08)]",
  },
};

const TINT_STYLES = {
  none: "",
  white: "bg-white/80",
  dark: "bg-ink/90",
};

export const Material = forwardRef<HTMLDivElement, MaterialProps>(
  ({ className, children, weight = "regular", elevated = true, tint = "none", blur, ...props }, ref) => {
    const reducedTransparency = useReducedTransparency();
    const highContrast = useHighContrast();
    
    // Apply reduced transparency: make surfaces frostier/solid
    const effectiveWeight = reducedTransparency ? "ultra" : weight;
    const effectiveTint = highContrast ? "white" : tint;
    const styles = MATERIAL_STYLES[effectiveWeight];
    
    return (
      <div
        ref={ref}
        className={cn(
          "backdrop-saturate-[180%]",
          styles.blur,
          styles.bg,
          styles.border,
          styles.shadow,
          elevated && "shadow-card",
          className
        )}
        style={{
          backgroundColor: effectiveTint === "dark" ? "rgba(15, 23, 42, 0.9)" : 
                           effectiveTint === "white" ? "rgba(255, 255, 255, 0.8)" : undefined,
          backdropFilter: reducedTransparency ? "blur(40px) saturate(180%)" : undefined,
        }}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Material.displayName = "Material";

/**
 * Toolbar/Navbar material - content scrolls underneath
 * Bright top edge = light catching the material
 */
export function Toolbar({ children, className, ...props }: { children: ReactNode; className?: string }) {
  const reducedTransparency = useReducedTransparency();
  
  return (
    <Material
      weight="regular"
      elevated
      className={cn(
        "sticky top-0 z-30 border-b",
        reducedTransparency ? "bg-white border-stone-200" : "border-white/40",
        className
      )}
      style={{
        background: reducedTransparency 
          ? "white" 
          : "rgba(255, 255, 255, 0.8)",
        backdropFilter: reducedTransparency ? "none" : "blur(20px) saturate(180%)",
        borderTop: "1px solid rgba(255, 255, 255, 0.4)",
      }}
      {...props}
    >
      {children}
    </Material>
  );
}

/**
 * Sheet/Modal material - dims background, pushes back
 * Materialize: animate blur radius and scale together on enter/exit
 */
interface SheetProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string;
  /** Position: "bottom" | "center" | "top" */
  position?: "bottom" | "center" | "top";
  /** Whether to show dimming scrim */
  modal?: boolean;
}

export function Sheet({ open, onClose, children, className, position = "bottom", modal = true }: SheetProps) {
  const reducedMotion = false; // Would use useReducedMotion()
  
  if (!open) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      {modal && (
        <div
          className="fixed inset-0 bg-ink/40 backdrop-blur-sm"
          onClick={onClose}
          style={{
            opacity: 1,
            transition: "opacity 200ms cubic-bezier(0.23, 1, 0.32, 1)",
          }}
          aria-hidden="true"
        />
      )}
      <Material
        weight="heavy"
        className={cn(
          "w-full max-w-[480px] rounded-t-[28px] rounded-b-none overflow-hidden",
          position === "center" && "rounded-[28px] my-auto max-h-[85vh]",
          position === "top" && "rounded-b-[28px] rounded-t-none",
          className
        )}
        style={{
          transform: "translateY(0)",
          transition: "transform 420ms cubic-bezier(0.32, 0.72, 0, 1)",
        }}
      >
        <div className="flex items-center justify-center px-4 py-3 border-b border-white/30">
          <div className="w-8 h-1.5 rounded-full bg-stone-300" aria-hidden="true" />
        </div>
        <div className="p-4 max-h-[70vh] overflow-y-auto">
          {children}
        </div>
      </Material>
    </div>
  );
}

/**
 * Popover material - origin-aware, never center
 * Anchor to trigger element
 */
interface PopoverProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string;
  /** Transform origin for anchored animation */
  origin?: string;
  /** Side: "top" | "bottom" | "left" | "right" */
  side?: "top" | "bottom" | "left" | "right";
  /** Alignment: "start" | "center" | "end" */
  align?: "start" | "center" | "end";
}

export function Popover({ open, onClose, children, className, origin = "top", side = "bottom", align = "center" }: PopoverProps) {
  const reducedMotion = false; // Would use useReducedMotion()
  
  if (!open) return null;
  
  const sideStyles = {
    top: "bottom-full mb-2",
    bottom: "top-full mt-2",
    left: "right-full mr-2",
    right: "left-full ml-2",
  };
  
  const alignStyles = {
    start: "items-start",
    center: "items-center",
    end: "items-end",
  };
  
  return (
    <div className="fixed z-50" style={{ transformOrigin: origin }}>
      <div
        className={cn(
          "flex",
          sideStyles[side],
          alignStyles[align],
          className
        )}
        style={{
          opacity: 1,
          transform: "scale(1)",
          transition: reducedMotion 
            ? "opacity 150ms ease" 
            : "opacity 180ms cubic-bezier(0.23, 1, 0.32, 1), transform 180ms cubic-bezier(0.23, 1, 0.32, 1)",
        }}
      >
        <Material weight="heavy" className="rounded-2xl p-3 shadow-card min-w-[200px] max-w-[360px]">
          {children}
        </Material>
      </div>
    </div>
  );
}

/**
 * Card material - for content cards
 */
interface CardProps extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
  weight?: MaterialProps["weight"];
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, interactive = false, weight = "regular", ...props }, ref) => {
    const reducedTransparency = useReducedTransparency();
    const effectiveWeight = reducedTransparency ? "ultra" : weight;
    
    return (
      <Material
        ref={ref}
        weight={effectiveWeight}
        className={cn(
          "rounded-2xl",
          interactive && "pressable cursor-pointer hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)]",
          className
        )}
        {...props}
      >
        {children}
      </Material>
    );
  }
);

Card.displayName = "Card";

/**
 * Scroll edge effect - fade mask instead of hard divider
 * Fade a small blur/gradient mask where content meets floating chrome
 */
export function ScrollEdge({ 
  children, 
  className, 
  position = "top",
  intensity = "medium"
}: { 
  children: ReactNode; 
  className?: string; 
  position?: "top" | "bottom";
  intensity?: "light" | "medium" | "strong";
}) {
  const gradients = {
    top: {
      light: "bg-gradient-to-b from-stone-50/90 via-stone-50/50 to-transparent",
      medium: "bg-gradient-to-b from-stone-50 via-stone-50/60 to-transparent",
      strong: "bg-gradient-to-b from-stone-100 via-stone-50/80 to-transparent",
    },
    bottom: {
      light: "bg-gradient-to-t from-stone-50/90 via-stone-50/50 to-transparent",
      medium: "bg-gradient-to-t from-stone-50 via-stone-50/60 to-transparent",
      strong: "bg-gradient-to-t from-stone-100 via-stone-50/80 to-transparent",
    },
  };
  
  return (
    <div className={cn("relative", className)}>
      {children}
      <div 
        className={cn(
          "absolute inset-x-0 h-8 pointer-events-none",
          position === "top" ? "top-0" : "bottom-0",
          gradients[position][intensity]
        )}
        aria-hidden="true"
      />
    </div>
  );
}