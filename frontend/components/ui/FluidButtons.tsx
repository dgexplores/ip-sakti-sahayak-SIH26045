"use client";

import { forwardRef, useRef, useCallback, type ButtonHTMLAttributes, type ReactNode } from "react";
import { animate, spring } from "motion";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/lib/motion";
import { hapticPress, hapticSuccess, hapticError, hapticSelection } from "@/lib/haptics";

/**
 * Apple Design: Buttons respond on pointer-down (not release)
 * Instant feedback, spring scale on press, interruptible
 */
export interface FluidButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "success";
  size?: "sm" | "md" | "lg" | "xl";
  loading?: boolean;
  loadingText?: string;
  icon?: ReactNode;
  iconPosition?: "left" | "right";
  fullWidth?: boolean;
  pressable?: boolean;
}

const VARIANT_STYLES = {
  primary: "bg-ink text-white hover:bg-ink/90 border-ink",
  secondary: "bg-white text-ink border-stone-200 hover:border-stone-300",
  ghost: "bg-transparent text-ink hover:bg-stone-100 border-transparent",
  danger: "bg-red-500 text-white hover:bg-red-600 border-red-600",
  success: "bg-emerald-600 text-white hover:bg-emerald-700 border-emerald-700",
} as const;

const SIZE_STYLES = {
  sm: "px-3 py-2 text-sm gap-1.5",
  md: "px-4 py-3 text-[15px] gap-2",
  lg: "px-6 py-4 text-[16px] gap-2",
  xl: "px-8 py-5 text-[17px] gap-2.5",
} as const;

export const FluidButton = forwardRef<HTMLButtonElement, FluidButtonProps>(
  ({ 
    className, 
    children, 
    variant = "primary", 
    size = "md", 
    loading = false, 
    loadingText,
    icon, 
    iconPosition = "left",
    fullWidth = false,
    pressable = true,
    disabled,
    onClick,
    ...props 
  }, ref) => {
    const reducedMotion = useReducedMotion();
    const scaleRef = { current: null as HTMLButtonElement | null };
    
    // Handle forwarded ref properly
    const combinedRef = useCallback((el: HTMLButtonElement | null) => {
      scaleRef.current = el;
      if (typeof ref === "function") {
        ref(el);
      } else if (ref && typeof ref === "object") {
        ref.current = el;
      }
    }, [ref]);

    const handlePointerDown = () => {
      if (disabled || loading || reducedMotion) return;
      if (!pressable) return;
      
      hapticPress();
      animate(scaleRef.current!, { scale: 0.96 }, { 
        type: "spring", 
        damping: 1.0, 
        stiffness: 300 
      });
    };

    const handlePointerUp = () => {
      if (disabled || loading || reducedMotion) return;
      if (!pressable) return;
      
      animate(scaleRef.current!, { scale: 1 }, { 
        type: "spring", 
        damping: 1.0, 
        stiffness: 300 
      });
    };

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (disabled || loading) {
        e.preventDefault();
        hapticError();
        return;
      }
      
      if (onClick) {
        onClick(e);
        if (!e.defaultPrevented) {
          hapticSuccess();
        }
      }
    };

    const baseStyles = cn(
      "pressable inline-flex items-center justify-center font-extrabold rounded-2xl border-2",
      "touch-48 transition-colors",
      VARIANT_STYLES[variant],
      SIZE_STYLES[size],
      fullWidth && "w-full",
      disabled && "opacity-40 cursor-not-allowed",
      loading && "cursor-wait",
      className
    );

    return (
      <button
        ref={combinedRef}
        className={baseStyles}
        disabled={disabled || loading}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
        onPointerCancel={handlePointerUp}
        onClick={handleClick}
        aria-busy={loading}
        aria-disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <>
            <span 
              className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white" 
              style={{ animation: "spin 0.7s linear infinite" }} 
              aria-hidden="true" 
            />
            <span>{loadingText ?? children}</span>
          </>
        ) : (
          <>
            {icon && iconPosition === "left" && <span className="flex-shrink-0">{icon}</span>}
            <span>{children}</span>
            {icon && iconPosition === "right" && <span className="flex-shrink-0">{icon}</span>}
          </>
        )}
      </button>
    );
  }
);

FluidButton.displayName = "FluidButton";

/**
 * Toggle button - Apple: respond on pointer-down, spring animation
 */
export interface FluidToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  className?: string;
}

export function FluidToggle({ 
  checked, 
  onChange, 
  label, 
  description, 
  size = "md",
  disabled = false,
  className 
}: FluidToggleProps) {
  const reducedMotion = useReducedMotion();
  const thumbRef = useRef<HTMLDivElement>(null);

  const handleChange = () => {
    if (disabled) {
      hapticError();
      return;
    }
    const next = !checked;
    onChange(next);
    multimodalFeedback(next ? "success" : "toggle", { hapticPattern: next ? "success" : "light" });
  };

  const trackSize = { sm: "w-8 h-5", md: "w-11 h-6", lg: "w-14 h-7" };
  const thumbSize = { sm: "w-4 h-4", md: "w-5 h-5", lg: "w-6 h-6" };
  const translate = { sm: "translate-x-4", md: "translate-x-5", lg: "translate-x-7" };

  return (
    <label className={cn("inline-flex items-center gap-3 cursor-pointer", className)}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        onClick={handleChange}
        onPointerDown={(e) => {
          if (disabled || reducedMotion) return;
          e.preventDefault();
          hapticPress();
        }}
        className={cn(
          "relative inline-flex shrink-0 rounded-full border-2 transition-all",
          trackSize[size],
          checked 
            ? "bg-saffron border-saffron" 
            : "bg-stone-200 border-stone-300 hover:border-stone-400",
          disabled && "opacity-40 cursor-not-allowed"
        )}
        style={{
          transition: reducedMotion 
            ? "background-color 150ms ease, border-color 150ms ease" 
            : "background-color 180ms cubic-bezier(0.23, 1, 0.32, 1), border-color 180ms cubic-bezier(0.23, 1, 0.32, 1)",
        }}
      >
        <span
          ref={thumbRef}
          className={cn(
            "absolute top-1/2 left-1 rounded-full bg-white shadow-[0_1px_3px_rgba(0,0,0,0.15)]",
            thumbSize[size],
            checked && translate[size]
          )}
          style={{
            transform: checked ? "translateX(100%) translateY(-50%)" : "translateY(-50%)",
            transition: reducedMotion
              ? "transform 150ms ease"
              : "transform 180ms cubic-bezier(0.34, 1.56, 0.64, 1)",
          }}
          aria-hidden="true"
        />
      </button>
      {(label || description) && (
        <div className="text-left">
          {label && <span className="block font-bold text-ink">{label}</span>}
          {description && <span className="block text-sm text-stone-500">{description}</span>}
        </div>
      )}
    </label>
  );
}

/**
 * Segmented control - Apple: fluid selection with spring
 */
export interface FluidSegmentedProps {
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string; icon?: ReactNode }>;
  className?: string;
  disabled?: boolean;
}

export function FluidSegmented({ value, onChange, options, className, disabled = false }: FluidSegmentedProps) {
  const reducedMotion = useReducedMotion();

  return (
    <div 
      role="tablist" 
      aria-label="Segmented control"
      className={cn(
        "inline-flex p-1 rounded-2xl bg-stone-100 border border-stone-200",
        className
      )}
    >
      {options.map((opt) => (
        <button
          key={opt.value}
          role="tab"
          aria-selected={value === opt.value}
          onClick={() => {
            if (disabled) return;
            onChange(opt.value);
            hapticSelection();
          }}
          disabled={disabled}
          className={cn(
            "pressable rounded-xl px-4 py-2.5 text-sm font-bold transition-all",
            "flex items-center gap-2 min-w-[80px] justify-center",
            value === opt.value
              ? "bg-white text-ink shadow-card"
              : "text-stone-600 hover:text-ink",
            disabled && "opacity-40 cursor-not-allowed"
          )}
          style={{
            transition: reducedMotion
              ? "all 150ms ease"
              : "all 180ms cubic-bezier(0.23, 1, 0.32, 1)",
          }}
        >
          {opt.icon && <span className="w-4 h-4">{opt.icon}</span>}
          <span>{opt.label}</span>
        </button>
      ))}
    </div>
  );
}

/**
 * Floating action button - spring entrance, press feedback
 */
export interface FluidFABProps extends Omit<FluidButtonProps, "fullWidth"> {
  position?: "bottom-right" | "bottom-left" | "top-right" | "top-left";
  expanded?: boolean;
  expandContent?: ReactNode;
}

export function FluidFAB({ 
  children, 
  onClick, 
  className, 
  position = "bottom-right",
  expanded = false,
  expandContent,
  variant = "primary",
  size = "lg",
  ...props 
}: FluidFABProps) {
  const reducedMotion = useReducedMotion();

  const positions = {
    "bottom-right": "fixed bottom-6 right-6",
    "bottom-left": "fixed bottom-6 left-6",
    "top-right": "fixed top-6 right-6",
    "top-left": "fixed top-6 left-6",
  };

  return (
    <div className={cn("z-40 flex flex-col items-end gap-3", positions[position])}>
      {expanded && expandContent && (
        <div
          className="flex items-center gap-3"
          style={{
            opacity: expanded ? 1 : 0,
            transform: expanded ? "translateX(0)" : "translateX(20px)",
            transition: reducedMotion
              ? "opacity 150ms ease, transform 150ms ease"
              : "opacity 200ms cubic-bezier(0.23, 1, 0.32, 1), transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1)",
          }}
        >
          {expandContent}
        </div>
      )}
      <FluidButton
        variant={variant}
        size={size}
        onClick={onClick}
        className={cn("rounded-full w-14 h-14 p-0 shadow-[0_4px_16px_rgba(0,0,0,0.12)]", className)}
        {...props}
      >
        {children}
      </FluidButton>
    </div>
  );
}

import { multimodalFeedback } from "@/lib/haptics";