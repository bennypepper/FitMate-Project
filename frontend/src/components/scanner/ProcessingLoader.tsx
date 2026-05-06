"use client";

import React from "react";

export default function ProcessingLoader() {
  return (
    <div className="absolute inset-0 z-50 flex flex-col items-center justify-center backdrop-blur-[20px] bg-surface/80">
      <div className="relative w-32 h-32 mb-6 shadow-ambient rounded-xl overflow-hidden bg-surface-container aspect-square border border-primary-container/20 flex items-center justify-center">
        {/* Simple scanning animation */}
        <div className="absolute top-0 left-0 w-full h-1 bg-primary-container shadow-[0_4px_10px_-2px_#930014]" 
             style={{ animation: 'scan 1.5s ease-in-out infinite alternate' }}></div>
        <div className="flex gap-2 text-primary-container opacity-50 relative z-10 font-cjk text-4xl">
           藥方
        </div>
      </div>
      <p className="text-on-surface font-sans font-medium text-lg animate-pulse text-center px-6">
        Menganalisis Komposisi TCM...
      </p>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scan {
          0% { transform: translateY(0); }
          100% { transform: translateY(128px); }
        }
      `}} />
    </div>
  );
}
