"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { projectMomentum, rubberband, springConfig, nearestSnapPoint } from "./motion";

export interface DragState {
  x: number;
  y: number;
  velocityX: number;
  velocityY: number;
  isDragging: boolean;
  startX: number;
  startY: number;
  offsetX: number;
  offsetY: number;
}

export interface DragHandlers {
  onDragStart?: (e: PointerEvent, state: DragState) => void;
  onDrag?: (e: PointerEvent, state: DragState) => void;
  onDragEnd?: (e: PointerEvent, state: DragState) => void;
  onClick?: (e: PointerEvent) => void;
}

export interface DragOptions {
  axis?: "x" | "y" | "both";
  bounds?: { minX?: number; maxX?: number; minY?: number; maxY?: number };
  rubberband?: boolean;
  hysteresis?: number; // px threshold before drag starts
  momentum?: boolean;
  snapPoints?: number[];
  onSnap?: (point: number) => void;
}

/**
 * Apple Design: Direct manipulation with 1:1 tracking
 * Respects grab offset, tracks velocity, supports momentum projection
 */
export function useDrag(
  elementRef: React.RefObject<HTMLElement>,
  handlers: DragHandlers,
  options: DragOptions = {}
) {
  const {
    axis = "both",
    bounds,
    rubberband: useRubberband = false,
    hysteresis = 10,
    momentum = false,
    snapPoints = [],
    onSnap,
  } = options;

  const stateRef = useRef<DragState>({
    x: 0, y: 0, velocityX: 0, velocityY: 0,
    isDragging: false, startX: 0, startY: 0, offsetX: 0, offsetY: 0
  });
  
  const historyRef = useRef<Array<{ x: number; y: number; t: number }>>([]);
  const animationRef = useRef<number>();
  const hasMovedRef = useRef(false);

  // Velocity calculation from position history
  const calculateVelocity = useCallback(() => {
    const now = performance.now();
    const recent = historyRef.current.filter(h => now - h.t < 100);
    if (recent.length < 2) return { vx: 0, vy: 0 };
    
    const first = recent[0];
    const last = recent[recent.length - 1];
    const dt = (last.t - first.t) / 1000; // seconds
    if (dt === 0) return { vx: 0, vy: 0 };
    
    return {
      vx: (last.x - first.x) / dt,
      vy: (last.y - first.y) / dt,
    };
  }, []);

  const pointerDown = useCallback((e: PointerEvent) => {
    const el = elementRef.current;
    if (!el) return;

    // Respect grab offset - don't snap to center
    const rect = el.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const offsetY = e.clientY - rect.top;

    // Capture pointer for continuous tracking outside element
    el.setPointerCapture(e.pointerId);

    stateRef.current = {
      x: e.clientX, y: e.clientY,
      velocityX: 0, velocityY: 0,
      isDragging: false, // Wait for hysteresis
      startX: e.clientX, startY: e.clientY,
      offsetX, offsetY,
    };
    historyRef.current = [{ x: e.clientX, y: e.clientY, t: performance.now() }];
    hasMovedRef.current = false;

    const moveHandler = (e: PointerEvent) => {
      const state = stateRef.current;
      const dx = e.clientX - state.startX;
      const dy = e.clientY - state.startY;
      const distance = Math.hypot(dx, dy);

      // Hysteresis threshold before committing to drag
      if (!state.isDragging && distance < hysteresis) return;

      if (!state.isDragging) {
        state.isDragging = true;
        hasMovedRef.current = true;
        handlers.onDragStart?.(e, state);
      }

      // Track velocity history
      historyRef.current.push({ x: e.clientX, y: e.clientY, t: performance.now() });
      if (historyRef.current.length > 10) historyRef.current.shift();

      const { vx, vy } = calculateVelocity();
      state.velocityX = vx;
      state.velocityY = vy;

      // Calculate new position with 1:1 tracking
      let newX = state.x + (e.clientX - state.x);
      let newY = state.y + (e.clientY - state.y);

      // Apply bounds with rubber-banding
      if (bounds) {
        if (bounds.minX !== undefined && newX < bounds.minX) {
          if (useRubberband) {
            const overshoot = bounds.minX - newX;
            newX = bounds.minX - rubberband(overshoot, bounds.maxX! - bounds.minX!);
          } else {
            newX = bounds.minX;
          }
        }
        if (bounds.maxX !== undefined && newX > bounds.maxX) {
          if (useRubberband) {
            const overshoot = newX - bounds.maxX;
            newX = bounds.maxX + rubberband(overshoot, bounds.maxX - bounds.minX!);
          } else {
            newX = bounds.maxX;
          }
        }
        if (bounds.minY !== undefined && newY < bounds.minY) {
          if (useRubberband) {
            const overshoot = bounds.minY - newY;
            newY = bounds.minY - rubberband(overshoot, bounds.maxY! - bounds.minY!);
          } else {
            newY = bounds.minY;
          }
        }
        if (bounds.maxY !== undefined && newY > bounds.maxY) {
          if (useRubberband) {
            const overshoot = newY - bounds.maxY;
            newY = bounds.maxY + rubberband(overshoot, bounds.maxY - bounds.minY!);
          } else {
            newY = bounds.maxY;
          }
        }
      }

      state.x = newX;
      state.y = newY;

      handlers.onDrag?.(e, state);
    };

    const upHandler = (e: PointerEvent) => {
      const state = stateRef.current;
      (e.target as Element)?.releasePointerCapture?.(e.pointerId);

      if (state.isDragging) {
        const { vx, vy } = calculateVelocity();
        state.velocityX = vx;
        state.velocityY = vy;
        handlers.onDragEnd?.(e, state);

        // Momentum projection for flick gestures
        if (momentum && snapPoints.length > 0) {
          const velocity = axis === "x" ? vx : axis === "y" ? vy : Math.hypot(vx, vy);
          const currentPos = axis === "x" ? state.x : axis === "y" ? state.y : state.x;
          const projected = currentPos + projectMomentum(velocity);
          const target = nearestSnapPoint(projected, snapPoints);
          onSnap?.(target);
        }
      } else if (!hasMovedRef.current) {
        // Tap - not a drag
        handlers.onClick?.(e);
      }

      // Cleanup
      window.removeEventListener("pointermove", moveHandler);
      window.removeEventListener("pointerup", upHandler);
      window.removeEventListener("pointercancel", upHandler);
    };

    window.addEventListener("pointermove", moveHandler);
    window.addEventListener("pointerup", upHandler);
    window.addEventListener("pointercancel", upHandler);
  }, [elementRef, handlers, axis, bounds, useRubberband, hysteresis, momentum, snapPoints, onSnap, calculateVelocity]);

  useEffect(() => {
    const el = elementRef.current;
    if (!el) return;
    el.addEventListener("pointerdown", pointerDown);
    return () => el.removeEventListener("pointerdown", pointerDown);
  }, [elementRef, pointerDown]);

  // Return current state for external use
  return stateRef.current;
}

/**
 * Horizontal swipe gesture for carousels, cards, drawers
 * Includes momentum projection and snap points
 */
export function useSwipe(
  elementRef: React.RefObject<HTMLElement>,
  onSwipe: (direction: "left" | "right", velocity: number) => void,
  options: { threshold?: number; hysteresis?: number } = {}
) {
  const { threshold = 50, hysteresis = 10 } = options;
  const startRef = useRef<{ x: number; t: number } | null>(null);

  useEffect(() => {
    const el = elementRef.current;
    if (!el) return;

    const down = (e: PointerEvent) => {
      startRef.current = { x: e.clientX, t: performance.now() };
      el.setPointerCapture(e.pointerId);
    };

    const up = (e: PointerEvent) => {
      if (!startRef.current) return;
      
      const dx = e.clientX - startRef.current.x;
      const dt = (performance.now() - startRef.current.t) / 1000;
      const velocity = dx / dt;

      if (Math.abs(dx) > threshold && dt < 0.5) {
        onSwipe(dx > 0 ? "right" : "left", velocity);
      }
      
      startRef.current = null;
      (e.target as Element)?.releasePointerCapture?.(e.pointerId);
    };

    el.addEventListener("pointerdown", down);
    el.addEventListener("pointerup", up);
    return () => {
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointerup", up);
    };
  }, [elementRef, onSwipe, threshold]);
}

/**
 * Pull-to-refresh / pull-down gesture with rubber-banding
 */
export function usePullDown(
  elementRef: React.RefObject<HTMLElement>,
  onRefresh: () => Promise<void>,
  options: { threshold?: number; resistance?: number } = {}
) {
  const { threshold = 80, resistance = 0.55 } = options;
  const [pullDistance, setPullDistance] = useState(0);
  const [isPulling, setIsPulling] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const startYRef = useRef<number | null>(null);

  useEffect(() => {
    const el = elementRef.current;
    if (!el) return;

    const down = (e: PointerEvent) => {
      if (el.scrollTop > 0) return; // Only at top
      startYRef.current = e.clientY;
      el.setPointerCapture(e.pointerId);
    };

    const move = (e: PointerEvent) => {
      if (startYRef.current === null || isRefreshing) return;
      
      const dy = e.clientY - startYRef.current;
      if (dy <= 0) return; // Only pull down
      
      setIsPulling(true);
      // Rubber-band resistance
      const distance = Math.min(dy * resistance, threshold * 1.5);
      setPullDistance(distance);
    };

    const up = async (e: PointerEvent) => {
      if (startYRef.current === null) return;
      
      const dy = e.clientY - startYRef.current;
      startYRef.current = null;
      (e.target as Element)?.releasePointerCapture?.(e.pointerId);
      
      if (pullDistance >= threshold && !isRefreshing) {
        setIsRefreshing(true);
        setPullDistance(threshold); // Hold at threshold during refresh
        try {
          await onRefresh();
        } finally {
          setIsRefreshing(false);
          // Animate back with spring
          setPullDistance(0);
        }
      } else {
        setPullDistance(0);
      }
      setIsPulling(false);
    };

    el.addEventListener("pointerdown", down);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    
    return () => {
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointercancel", up);
    };
  }, [elementRef, onRefresh, threshold, resistance, isRefreshing, pullDistance]);

  return { pullDistance, isPulling, isRefreshing };
}

/**
 * Tap with instant feedback (Apple: respond on pointer-down)
 */
export function usePress(
  onPress: () => void,
  options: { haptic?: boolean; delay?: number } = {}
) {
  const { haptic = true, delay = 0 } = options;
  const timeoutRef = useRef<number>();
  const pressedRef = useRef(false);

  const trigger = useCallback(() => {
    if (pressedRef.current) return;
    pressedRef.current = true;
    onPress();
    if (haptic && "vibrate" in navigator) {
      navigator.vibrate(10);
    }
    setTimeout(() => { pressedRef.current = false; }, delay || 150);
  }, [onPress, haptic, delay]);

  useEffect(() => {
    return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); };
  }, []);

  return {
    onPointerDown: trigger,
    onClick: () => {}, // Prevent default click if handled by pointer-down
  };
}