"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { animate, AnimationPlaybackControls, spring } from "motion";

/**
 * Apple Design: Spring parameters mapped from damping ratio + response
 * damping: 1.0 = critically damped (no overshoot)
 * damping: 0.8 = under-damped (slight bounce for momentum interactions)
 * response: time to reach target in seconds
 */
export const SPRINGS = {
  default: { type: "spring", damping: 1.0, stiffness: 100 } as const,
  snappy: { type: "spring", damping: 1.0, stiffness: 150 } as const,
  momentum: { type: "spring", damping: 0.8, stiffness: 100 } as const,
  drawer: { type: "spring", damping: 0.8, stiffness: 120 } as const,
  popover: { type: "spring", damping: 1.0, stiffness: 180 } as const,
  button: { type: "spring", damping: 1.0, stiffness: 200 } as const,
  scale: { type: "spring", damping: 1.0, stiffness: 300 } as const,
} as const;

/**
 * Convert Apple's damping + response to Motion's spring config
 * response ≈ 2π / sqrt(stiffness) for critically damped
 */
export function springConfig(damping: number, response: number) {
  const stiffness = Math.pow(2 * Math.PI / response, 2);
  return { type: "spring", damping, stiffness } as const;
}

/**
 * Animate a value with spring, interruptible by default
 * Starts from current presentation value (not target)
 */
export function useSpringValue(initialValue: number) {
  const [value, setValue] = useState(initialValue);
  const animationRef = useRef<AnimationPlaybackControls | null>(null);

  const animateTo = useCallback((
    target: number,
    config: { damping?: number; response?: number; velocity?: number } = {}
  ) => {
    const { damping = 1.0, response = 0.35, velocity = 0 } = config;
    
    // Kill any in-flight animation (interruptibility)
    if (animationRef.current) {
      animationRef.current.stop();
    }

    // Animate from current presentation value
    animationRef.current = animate(
      value,
      target,
      {
        type: "spring",
        damping,
        stiffness: Math.pow(2 * Math.PI / response, 2),
        velocity,
        onUpdate: (v) => setValue(v),
      }
    );
  }, []);

  const setImmediate = useCallback((target: number) => {
    if (animationRef.current) {
      animationRef.current.stop();
    }
    setValue(target);
  }, []);

  return { value, animateTo, setImmediate, stop: () => animationRef.current?.stop() };
}

/**
 * Spring animation for any numeric value with interruptibility
 */
export function springAnimate(
  getCurrent: () => number,
  setValue: (v: number) => void,
  target: number,
  options: { damping?: number; response?: number; velocity?: number; onComplete?: () => void } = {}
) {
  const { damping = 1.0, response = 0.35, velocity = 0, onComplete } = options;
  
  return animate(
    getCurrent(),
    target,
    {
      type: "spring",
      damping,
      stiffness: Math.pow(2 * Math.PI / response, 2),
      velocity,
      onUpdate: (v) => setValue(v),
    }
  ).finished.then(onComplete);
}

/**
 * Apple's momentum projection function
 * decelerationRate ≈ 0.998 for normal scroll feel; 0.99 for snappier
 */
export function projectMomentum(
  initialVelocity: number, // px/s
  decelerationRate = 0.998
): number {
  return (initialVelocity / 1000) * decelerationRate / (1 - decelerationRate);
}

/**
 * Find nearest snap point from projected endpoint
 */
export function nearestSnapPoint(position: number, snapPoints: number[]): number {
  return snapPoints.reduce((nearest, point) => 
    Math.abs(point - position) < Math.abs(nearest - position) ? point : nearest
  , snapPoints[0]);
}

/**
 * Rubber-band function for soft boundaries
 * The further past the bound, the less the element follows
 */
export function rubberband(
  overshoot: number, // how far past boundary
  dimension: number, // viewport/container dimension
  constant = 0.55
): number {
  return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot));
}

/**
 * Staggered entrance animation delays
 */
export function staggerDelay(index: number, baseDelay = 48): number {
  return index * baseDelay;
}

/**
 * Reduced motion detection
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mediaQuery.matches);
    
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);
  
  return reduced;
}

/**
 * Reduced transparency detection
 */
export function useReducedTransparency(): boolean {
  const [reduced, setReduced] = useState(false);
  
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-transparency: reduce)");
    setReduced(mediaQuery.matches);
    
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);
  
  return reduced;
}

/**
 * High contrast detection
 */
export function useHighContrast(): boolean {
  const [highContrast, setHighContrast] = useState(false);
  
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-contrast: more)");
    setHighContrast(mediaQuery.matches);
    
    const handler = (e: MediaQueryListEvent) => setHighContrast(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);
  
  return highContrast;
}

/**
 * Spring-based fade in/out for reduced motion
 */
export function fadeSpring(reducedMotion: boolean) {
  if (reducedMotion) {
    return { opacity: 1, transition: { duration: 0.15 } };
  }
  return { opacity: 1, transition: { type: "spring", damping: 1.0, stiffness: 100 } };
}