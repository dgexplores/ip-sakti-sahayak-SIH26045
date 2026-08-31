"use client";
import { useState, useRef } from "react";
import { Icon } from "@/components/Icon";
import { t } from "@/lib/i18n";

export function VoiceButton({ onTranscript, lang = "hi" }: { onTranscript: (v: string) => void; lang?: string }) {
  const s = t(lang);
  const [recording, setRecording] = useState(false);
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
      alert(s.errorHint);
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
      aria-label={recording ? s.listening : s.speak}
      className={`pressable touch-48 relative inline-flex items-center gap-3 px-6 py-4 rounded-[20px] font-bold text-[17px] leading-none shadow-card border-2 transition-colors ${recording ? "bg-red-500 border-red-600 text-white" : "bg-white border-stone-200 text-ink hover:border-stone-300"}`}
      style={{ transformOrigin: "center" }}
    >
      <span className={`w-10 h-10 rounded-full grid place-items-center text-lg shrink-0 ${recording ? "bg-white text-red-500 animate-pulse" : "bg-saffron text-white"}`}>
        {recording ? <Icon name="stop" className="w-4 h-4 fill-current" /> : <Icon name="voice" className="w-5 h-5" />}
      </span>
      <span className="text-left">
        <span className="block">{recording ? s.listening : s.speak}</span>
        <span className={`block text-xs font-medium ${recording ? "text-red-100" : "text-stone-500"}`}>{recording ? s.listeningHint : s.speakHint}</span>
      </span>
      {recording && <span className="absolute inset-0 rounded-[20px] border-2 border-red-300 pointer-events-none" style={{ animation: "ping 1.2s cubic-bezier(0,0,0.2,1) infinite" }} aria-hidden />}
    </button>
  );
}
