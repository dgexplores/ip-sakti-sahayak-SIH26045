"use client";

import { useState, useRef, useEffect, useCallback, type ReactNode } from "react";
import { animate } from "motion";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/lib/motion";
import { useDrag } from "@/lib/gestures";
import { hapticSnap, hapticSuccess } from "@/lib/haptics";
import { Material } from "./Materials";

/**
 * Apple Design: Drawer/sheet with spring animation
 * Interruptible, velocity handoff, rubber-banding at edges
 * Enter and exit along same path
 */
export interface FluidDrawerProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  className?: string;
  /** Snap points as fractions of viewport height (0 = top, 1 = bottom) */
  snapPoints?: number[];
  /** Default snap point index */
  defaultSnap?: number;
  /** Whether dragging the content area can move the drawer */
  dragContent?: boolean;
  /** Show drag handle */
  showHandle?: boolean;
  /** Maximum height as viewport fraction */
  maxHeight?: number;
}

export function FluidDrawer({ 
  open, 
  onClose, 
  children, 
  title,
  className,
  snapPoints = [0.25, 0.5, 0.9],
  defaultSnap = 1,
  dragContent = true,
  showHandle = true,
  maxHeight = 0.9,
}: FluidDrawerProps) {
  const reducedMotion = useReducedMotion();
  const drawerRef = useRef<HTMLDivElement>(null);
  const handleRef = useRef<HTMLButtonElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  
  const [position, setPosition] = useState(defaultSnap);
  const [isDragging, setIsDragging] = useState(false);
  const animationRef = useRef<any>(null);

  const vh = typeof window !== "undefined" ? window.innerHeight : 800;
  const maxPx = vh * maxHeight;
  const snapPx = snapPoints.map(p => vh * (1 - p)); // Distance from top

  // Animate to snap point with spring
  const animateToSnap = useCallback((snapIndex: number, velocity = 0) => {
    if (animationRef.current) animationRef.current.stop();
    
    const targetY = snapPx[snapIndex];
    const drawer = drawerRef.current;
    if (!drawer) return;

    animationRef.current = animate(
      drawer,
      { y: targetY },
      {
        type: "spring",
        damping: velocity !== 0 ? 0.8 : 1.0, // Bounce if flicked
        stiffness: 120,
        velocity,
      }
    ).finished.then(() => {
      setPosition(snapIndex);
    });
  }, []);

  // Drag handler for the handle
  const handleState = useDrag(
    handleRef,
    {
      onDragStart: () => setIsDragging(true),
      onDrag: (_e, state) => {
        const drawer = drawerRef.current;
        if (drawer) {
          // Clamp to max height
          const y = Math.max(snapPx[0], Math.min(state.y, snapPx[snapPx.length - 1]));
          drawer.style.transform = `translateY(${y}px)`;
        }
      },
      onDragEnd: (_e, state) => {
        setIsDragging(false);
        // Find nearest snap point with momentum projection
        const currentY = state.y;
        const velocity = state.velocityY;
        
        // Project momentum
        let projectedY = currentY;
        if (Math.abs(velocity) > 100) {
          // Simple projection
          projectedY = currentY + velocity * 0.1;
        }
        
        // Find nearest snap
        let nearest = 0;
        let minDist = Infinity;
        snapPx.forEach((p, i) => {
          const dist = Math.abs(p - projectedY);
          if (dist < minDist) {
            minDist = dist;
            nearest = i;
          }
        });
        
        animateToSnap(nearest, velocity / 1000);
        hapticSnap();
      },
    },
    { axis: "y", bounds: { minY: snapPx[0], maxY: snapPx[snapPx.length - 1] }, hysteresis: 8 }
  );

  // Drag handler for content area (scroll-aware)
  const contentState = useDrag(
    contentRef,
    {
      onDragStart: (e) => {
        const content = contentRef.current;
        if (content && content.scrollTop > 0) return; // Don't drag if scrollable
        setIsDragging(true);
      },
      onDrag: (_e, state) => {
        const content = contentRef.current;
        if (content && content.scrollTop > 0) return;
        const drawer = drawerRef.current;
        if (drawer) {
          const y = Math.max(snapPx[0], Math.min(state.y, snapPx[snapPx.length - 1]));
          drawer.style.transform = `translateY(${y}px)`;
        }
      },
      onDragEnd: (_e, state) => {
        setIsDragging(false);
        const velocity = state.velocityY;
        const currentY = state.y;
        
        // Project momentum
        let projectedY = currentY;
        if (Math.abs(velocity) > 100) {
          projectedY = currentY + velocity * 0.1;
        }
        let nearest = 0;
        let minDist = Infinity;
        snapPx.forEach((p, i) => {
          const dist = Math.abs(p - projectedY);
          if (dist < minDist) {
            minDist = dist;
            nearest = i;
          }
        });
        animateToSnap(nearest, velocity / 1000);
        hapticSnap();
      },
    },
    { axis: "y", bounds: { minY: snapPx[0], maxY: snapPx[snapPx.length - 1] }, hysteresis: 8 }
  );

  // Sync position when open changes
  useEffect(() => {
    if (open) {
      animateToSnap(defaultSnap);
    } else {
      const drawer = drawerRef.current;
      if (drawer) {
        animate(drawer, { y: vh }, { type: "spring", damping: 1.0, stiffness: 120 })
          .finished.then(onClose);
      }
    }
  }, [open, defaultSnap, animateToSnap, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-labelledby={title ? "drawer-title" : undefined}>
      {/* Scrim - tap to close */}
      <div
        className="fixed inset-0 bg-ink/40 backdrop-blur-sm"
        onClick={onClose}
        style={{
          opacity: 1,
          transition: reducedMotion 
            ? "opacity 150ms ease" 
            : "opacity 200ms cubic-bezier(0.23, 1, 0.32, 1)",
        }}
        aria-hidden="true"
      />
      
      {/* Drawer */}
      <div
        ref={drawerRef}
        className={cn("fixed left-0 right-0", className)}
        style={{
          transform: `translateY(${snapPx[position]}px)`,
          transition: "none", // Handled by spring animation
        }}
      >
        <Material weight="heavy" className="rounded-t-[28px] overflow-hidden max-h-[90vh]">
          {/* Handle */}
          {showHandle && (
            <button
              ref={handleRef}
              type="button"
              className="w-full flex justify-center py-3 touch-48 -mt-2"
              aria-label="Drag to resize"
            >
              <div className="w-8 h-1.5 rounded-full bg-stone-300" aria-hidden="true" />
            </button>
          )}
          
          {/* Header */}
          {title && (
            <div className="px-4 py-3 border-b border-white/30 flex items-center justify-between">
              <h2 id="drawer-title" className="h-display text-lg font-extrabold">{title}</h2>
              <button
                type="button"
                onClick={onClose}
                className="pressable touch-48 p-2 rounded-xl hover:bg-stone-100"
                aria-label="Close"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
          
          {/* Content - draggable */}
          <div
            ref={contentRef}
            className="max-h-[80vh] overflow-y-auto"
            style={{
              touchAction: dragContent ? "pan-y" : "auto",
            }}
          >
            {children}
          </div>
        </Material>
      </div>
    </div>
  );
}

/**
 * Fluid Popover - anchored, interruptible, origin-aware
 */
export interface FluidPopoverProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  anchorRef: React.RefObject<HTMLElement>;
  side?: "top" | "bottom" | "left" | "right";
  align?: "start" | "center" | "end";
  className?: string;
  offset?: number;
}

export function FluidPopover({ 
  open, 
  onClose, 
  children, 
  anchorRef, 
  side = "bottom", 
  align = "center",
  className,
  offset = 8,
}: FluidPopoverProps) {
  const reducedMotion = useReducedMotion();
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open || !anchorRef.current || !popoverRef.current) return;
    
    const anchor = anchorRef.current.getBoundingClientRect();
    const popover = popoverRef.current.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    
    let top = 0, left = 0;
    
    // Calculate position
    if (side === "bottom") {
      top = anchor.bottom + offset;
      if (align === "start") left = anchor.left;
      else if (align === "center") left = anchor.left + anchor.width / 2 - popover.width / 2;
      else left = anchor.right - popover.width;
    } else if (side === "top") {
      top = anchor.top - offset - popover.height;
      if (align === "start") left = anchor.left;
      else if (align === "center") left = anchor.left + anchor.width / 2 - popover.width / 2;
      else left = anchor.right - popover.width;
    }
    
    // Clamp to viewport
    left = Math.max(8, Math.min(left, vw - popover.width - 8));
    top = Math.max(8, Math.min(top, vh - popover.height - 8));
    
    popoverRef.current.style.transform = `translate(${left}px, ${top}px)`;
    popoverRef.current.style.transformOrigin = side === "bottom" ? "top" : "bottom";
  }, [open, anchorRef, side, align, offset]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div
        ref={popoverRef}
        className={cn("fixed z-50 pointer-events-auto", className)}
        style={{
          opacity: 1,
          transform: "scale(1)",
          transition: reducedMotion
            ? "opacity 100ms ease, transform 100ms ease"
            : "opacity 180ms cubic-bezier(0.23, 1, 0.32, 1), transform 180ms cubic-bezier(0.34, 1.56, 0.64, 1)",
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
 * Context menu - instant appearance, spring scale from origin
 */
export interface FluidContextMenuProps {
  open: boolean;
  onClose: () => void;
  items: Array<{
    label: string;
    onClick: () => void;
    icon?: ReactNode;
    disabled?: boolean;
    danger?: boolean;
    dividerAfter?: boolean;
  }>;
  x: number;
  y: number;
}

export function FluidContextMenu({ open, onClose, items, x, y }: FluidContextMenuProps) {
  const reducedMotion = useReducedMotion();
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div
        ref={menuRef}
        className="fixed pointer-events-auto"
        style={{
          left: x,
          top: y,
          transformOrigin: "top left",
          opacity: 1,
          transform: "scale(1)",
          transition: reducedMotion
            ? "opacity 80ms ease, transform 80ms ease"
            : "opacity 120ms cubic-bezier(0.23, 1, 0.32, 1), transform 120ms cubic-bezier(0.34, 1.56, 0.64, 1)",
        }}
      >
        <Material weight="heavy" className="rounded-2xl p-1.5 shadow-[0_8px_32px_rgba(0,0,0,0.12)] min-w-[180px]">
          {items.map((item, i) => (
            <button
              key={i}
              type="button"
              onClick={() => { item.onClick(); onClose(); hapticSuccess(); }}
              disabled={item.disabled}
              className={cn(
                "pressable w-full px-3 py-2.5 rounded-xl text-left text-sm font-medium flex items-center gap-3",
                "transition-colors",
                item.danger 
                  ? "text-red-600 hover:bg-red-50" 
                  : "text-ink hover:bg-stone-100",
                item.disabled && "opacity-40 cursor-not-allowed"
              )}
              style={{
                transition: "background-color 100ms ease, color 100ms ease",
              }}
            >
              {item.icon && <span className="w-5 h-5">{item.icon}</span>}
              <span>{item.label}</span>
            </button>
          ))}
        </Material>
      </div>
    </div>
  );
}