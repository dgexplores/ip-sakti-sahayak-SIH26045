"use client";
import { useEffect } from "react";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[#FFFBF5] grid place-items-center p-6">
      <div className="max-w-md w-full rounded-[20px] bg-white border-2 border-stone-200 shadow-card p-6 text-center space-y-4 stagger-in">
        <div className="w-12 h-12 mx-auto rounded-xl bg-red-500 text-white grid place-items-center text-xl font-extrabold">!</div>
        <div>
          <h1 className="h-display text-lg font-extrabold leading-tight">Kuch gadbad ho gayi</h1>
          <p className="text-sm text-stone-600 leading-relaxed mt-2">
            Something broke on this page. Your question and answer trace are still safe, this is
            just a display error. Try again, or refresh if it keeps happening.
          </p>
        </div>
        <button
          onClick={reset}
          className="pressable touch-48 w-full py-3 rounded-2xl bg-ink text-white text-[15px] font-extrabold"
        >
          Phir se koshish karo → Try again
        </button>
      </div>
    </div>
  );
}
