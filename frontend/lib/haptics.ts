"use client";

import { useRef, useCallback } from "react";

/**
 * Apple Design: Multimodal feedback — motion + sound + haptics
 * Three rules: Causality, Harmony, Utility
 */

// Haptic patterns for different interaction types
export const HAPTICS = {
  // Light tap - for button presses, toggles
  light: [10],
  press: [10], // alias for light
  // Medium - for successful actions, snaps
  medium: [15],
  // Heavy - for errors, important confirmations
  heavy: [25],
  // Selection - for picker changes, tab switches
  selection: [5, 50, 5],
  // Success - for completed actions
  success: [10, 50, 10, 50, 10],
  // Error - for failures, blocks
  error: [30, 100, 30],
  // Warning - for cautions
  warning: [15, 50, 15, 50, 15],
  // Snap/magnetic - quick pop
  snap: [12],
} as const;

type HapticPattern = keyof typeof HAPTICS;

/**
 * Check if haptics are supported
 */
export function isHapticsSupported(): boolean {
  return "vibrate" in navigator;
}

/**
 * Play haptic feedback with causality - tied to the actual causal event
 */
export function haptic(pattern: HapticPattern = "light"): void {
  if (!isHapticsSupported()) return;
  
  try {
    navigator.vibrate(HAPTICS[pattern]);
  } catch {
    // Silently fail - haptics are enhancement, not requirement
  }
}

/**
 * Play haptic for button press (respond on pointer-down)
 */
export function hapticPress(): void {
  haptic("light");
}

/**
 * Play haptic for successful commit/action
 */
export function hapticSuccess(): void {
  haptic("success");
}

/**
 * Play haptic for error/blocked action
 */
export function hapticError(): void {
  haptic("error");
}

/**
 * Play haptic for warning/caution
 */
export function hapticWarning(): void {
  haptic("warning");
}

/**
 * Play haptic for selection change (tabs, pickers)
 */
export function hapticSelection(): void {
  haptic("selection");
}

/**
 * Play haptic for snap/magnetic moment
 */
export function hapticSnap(): void {
  haptic("medium");
}

/**
 * Subtle audio feedback using Web Audio API
 * Only for meaningful moments, same frame as visual/haptic
 */

let audioContext: AudioContext | null = null;

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  return audioContext;
}

/**
 * Generate a simple tone
 */
function playTone(frequency: number, duration: number, type: OscillatorType = "sine", volume = 0.05): void {
  try {
    const ctx = getAudioContext();
    if (ctx.state === "suspended") ctx.resume();
    
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    oscillator.type = type;
    oscillator.frequency.value = frequency;
    
    gainNode.gain.setValueAtTime(0, ctx.currentTime);
    gainNode.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + duration);
  } catch {
    // Silently fail
  }
}

/**
 * Audio cues for key interactions
 */
export const AUDIO = {
  // Button press - subtle click
  press: () => playTone(800, 0.05, "square", 0.03),
  // Success - ascending major chord
  success: () => {
    playTone(523.25, 0.1); // C5
    setTimeout(() => playTone(659.25, 0.1), 50); // E5
    setTimeout(() => playTone(783.99, 0.15), 100); // G5
  },
  // Error - descending minor
  error: () => {
    playTone(440, 0.15, "triangle", 0.04); // A4
    setTimeout(() => playTone(349.23, 0.2), 80); // F4
  },
  // Warning - double beep
  warning: () => {
    playTone(600, 0.08, "sine", 0.04);
    setTimeout(() => playTone(600, 0.08, "sine", 0.04), 120);
  },
  // Snap/magnetic - quick pop
  snap: () => playTone(1000, 0.03, "sine", 0.02),
  // Toggle on/off
  toggle: (on: boolean) => playTone(on ? 600 : 400, 0.06, "sine", 0.03),
} as const satisfies Record<string, (...args: any[]) => void>;

/**
 * Combined multimodal feedback - fires on same frame
 * Causality: tied to actual event
 * Harmony: visual, audio, haptic simultaneous
 * Utility: only for meaningful moments
 */
export function multimodalFeedback(
  type: "press" | "success" | "error" | "warning" | "snap" | "toggle",
  options: { haptic?: boolean; audio?: boolean; visual?: boolean; hapticPattern?: HapticPattern } = {}
) {
  const { haptic: useHaptic = true, audio: useAudio = true, visual = true, hapticPattern } = options;
  
  // All fire together - same frame
  if (useHaptic) {
    if (type === "toggle") {
      // Toggle needs on/off state
    } else {
      haptic(hapticPattern ?? type);
    }
  }
  
  if (useAudio) {
    if (type === "toggle") {
      AUDIO.toggle(true);
    } else {
      (AUDIO[type as keyof typeof AUDIO] as (() => void) | undefined)?.();
    }
  }
  
  // Visual is handled by the component's spring animation
  return visual;
}

/**
 * Button press with instant feedback (Apple: respond on pointer-down)
 */
export function useButtonPress(
  onPress: () => void,
  options: { haptic?: boolean; audio?: boolean } = {}
) {
  const { haptic = true, audio = true } = options;
  const pressedRef = useRef(false);

  const handlePointerDown = useCallback(() => {
    if (pressedRef.current) return;
    pressedRef.current = true;
    
    // Instant multimodal feedback on pointer-down
    multimodalFeedback("press", { haptic, audio });
    
    onPress();
    
    setTimeout(() => { pressedRef.current = false; }, 150);
  }, [onPress, haptic, audio]);

  return { onPointerDown: handlePointerDown };
}