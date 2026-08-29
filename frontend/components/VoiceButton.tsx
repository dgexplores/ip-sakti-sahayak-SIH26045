"use client";
import { useState, useRef } from "react";

export function VoiceButton({ onTranscript, lang = "hi" }: { onTranscript: (t: string) => void; lang?: string }) {
  const [recording, setRecording] = useState(false);
  const [ Perecording, setPerecording] = useState(false);
  const recRef = useRef<any>(null);

  async function toggle() {
    if (recording) {
      recRef.current?.stop();
      setRecording(false);
      return;
    }
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    if (!SpeechRecognition) {
      // No browser STT — fallback: show prompt to type, but keep button visible for trust
      alert("Voice not supported on this browser. Type your question — or try Chrome on phone.");
      return;
    }
    const rec = new SpeechRecognition();
    rec.lang = lang === "hi" ? "hi-IN" : lang === "ta" ? "ta-IN" : lang === "kn" ? "kn-IN" : "en-IN";
    rec.interimResults = false;
    rec.onstart = () => setRecording(true);
    rec.onend = () => setRecording(false);
    rec.onresult = (e: any) => {
      const text = e.results[0][0].transcript;
      onTranscript(text);
    };
    rec.onerror = () => setRecording(false);
    recRef.current = rec;
    rec.start();
  }

  return (
    <button
      onClick={toggle}
      aria-pressed={recording}
      aria-label={recording ? "Stop recording" : "Tap to speak your question"}
      className={`pressable touch-48 relative inline-flex items-center gap-3 px-6 py-4 rounded-[20px] font-bold text-[17px] leading-none shadow-card border-2 transition-colors ${recording ? "bg-red-500 border-red-600 text-white" : "bg-white border-stone-200 text-ink hover:border-stone-300"}`}
      style={{ transformOrigin: "center" }}
    >
      <span className={`w-10 h-10 rounded-full grid place-items-center text-lg shrink-0 ${recording ? "bg-white text-red-500 animate-pulse" : "bg-saffron text-white"}`}>
        {recording ? "■" : "🎙️"}
      </span>
      <span className="text-left">
        <span className="block">{recording ? "Listening… tap to stop" : "Boliye — tap to speak"}</span>
        <span className={`block text-xs font-medium ${recording ? "text-red-100" : "text-stone-500"}`}>{recording ? "Humein sunai de raha hai" : "Hindi · Tamil · English — no typing needed"}</span>
      </span>
      {recording && <span className="absolute inset-0 rounded-[20px] border-2 border-red-300 pointer-events-none" style={{ animation: "ping 1.2s cubic-bezier(0,0,0.2,1) infinite" }} aria-hidden />}
    </button>
  );
}
