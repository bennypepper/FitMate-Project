"use client";

import React from "react";

export default function ProcessingLoader() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="absolute inset-0 z-50 flex flex-col items-center justify-center backdrop-blur-[16px] bg-paper/85 rounded-[inherit]"
    >
      <div className="relative w-32 h-32 mb-6 shadow-md rounded-xl overflow-hidden bg-card aspect-square border border-heritage/20 flex items-center justify-center">
        {/* Scanning animation */}
        <div className="absolute inset-x-0 h-1 bg-heritage animate-scan-sweep shadow-[0_4px_10px_-2px_rgba(122,34,48,0.65)]" />
        <div className="flex gap-2 text-heritage/60 relative z-10 font-chinese text-4xl select-none">
          藥方
        </div>
      </div>
      <p className="text-ink font-serif font-semibold text-lg animate-pulse text-center px-6">
        Menganalisis Komposisi TCM...
      </p>
    </div>
  );
}
