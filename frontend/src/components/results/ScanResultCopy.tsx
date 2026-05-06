"use client";

import { useState } from "react";

interface ScanResultCopyProps {
  ingredients: any[];
}

function buildCopyText(ingredients: any[]): string {
  if (!ingredients || ingredients.length === 0) {
    return "Tidak ada bahan yang terdeteksi.";
  }

  const lines: string[] = ["🔍 *Hasil Scan FitMate:*", "Bahan yang terdeteksi:", ""];

  for (const item of ingredients) {
    const name = item.indonesian_name || item.matched_mandarin || item.detected_text || "-";
    const emoji =
      item.category === "toxic" || item.category === "contraindicated"
        ? "⚠️"
        : item.category === "safe"
        ? "✅"
        : "❓";
    lines.push(`${emoji} ${name}`);
  }

  lines.push("");
  lines.push(
    "Tolong bantu saya memahami lebih lanjut tentang bahan-bahan di atas. " +
      "Apakah aman dikonsumsi? Ada kontraindikasi yang perlu diperhatikan?"
  );

  return lines.join("\n");
}

export default function ScanResultCopy({ ingredients }: ScanResultCopyProps) {
  const [copied, setCopied] = useState(false);

  const copyText = buildCopyText(ingredients);
  const waNumber = "14155238886";
  const waUrl = `https://wa.me/${waNumber}?text=${encodeURIComponent(copyText)}`;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(copyText);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = copyText;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  };

  return (
    <div className="mt-10 w-full">
      {/* Divider */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 h-px bg-light/40" />
        <span className="text-xs font-body text-on-surface-variant font-semibold tracking-widest uppercase">
          Konsultasi Lanjutan
        </span>
        <div className="flex-1 h-px bg-light/40" />
      </div>

      {/* Card */}
      <div className="rounded-2xl border border-light/50 bg-background shadow-sm overflow-hidden">
        {/* Header */}
        <div className="bg-[#25D366]/10 border-b border-[#25D366]/20 px-6 py-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-[#25D366] flex items-center justify-center flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="white" viewBox="0 0 16 16">
              <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.9 7.9 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.9 7.9 0 0 0 13.6 2.326zM7.994 14.521a6.6 6.6 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.56 6.56 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592m3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.73.73 0 0 0-.529.247c-.182.198-.691.677-.691 1.654s.71 1.916.81 2.049c.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232" />
            </svg>
          </div>
          <div>
            <p className="font-headline font-bold text-dark text-sm">
              Tanya Chatbot FitMate
            </p>
            <p className="font-body text-xs text-on-surface-variant">
              Dapatkan penjelasan mendalam dari chatbot kami
            </p>
          </div>
        </div>

        {/* Preview of copy content */}
        <div className="px-6 py-4">
          <p className="font-body text-xs text-on-surface-variant mb-3 font-medium">
            Pesan yang akan dikirim:
          </p>
          <div className="bg-slate-50 rounded-xl px-4 py-3 border border-slate-100 font-body text-xs text-on-surface leading-relaxed whitespace-pre-line max-h-28 overflow-y-auto">
            {copyText}
          </div>
        </div>

        {/* Action buttons */}
        <div className="px-6 pb-6 flex flex-col sm:flex-row gap-3">
          {/* Copy button */}
          <button
            onClick={handleCopy}
            className={`
              flex items-center justify-center gap-2 flex-1 px-4 py-3 rounded-xl
              font-body font-bold text-sm transition-all duration-200
              ${copied
                ? "bg-green-500 text-white"
                : "bg-dark text-white hover:bg-dark/90 active:scale-[0.98]"
              }
            `}
          >
            {copied ? (
              <>
                <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  check_circle
                </span>
                Tersalin!
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]">content_copy</span>
                Salin Pesan
              </>
            )}
          </button>

          {/* Open in WhatsApp directly */}
          <a
            href={waUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 flex-1 px-4 py-3 rounded-xl bg-[#25D366] text-white font-body font-bold text-sm hover:brightness-105 active:scale-[0.98] transition-all duration-150"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.9 7.9 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.9 7.9 0 0 0 13.6 2.326zM7.994 14.521a6.6 6.6 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.56 6.56 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592m3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.73.73 0 0 0-.529.247c-.182.198-.691.677-.691 1.654s.71 1.916.81 2.049c.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232" />
            </svg>
            Buka di WhatsApp
          </a>
        </div>

        {/* Instruction */}
        <div className="px-6 pb-5 -mt-2">
          <p className="font-body text-[11px] text-on-surface-variant text-center leading-relaxed">
            💡 Salin pesan di atas, lalu kirimkan ke chatbot WhatsApp FitMate untuk konsultasi lebih lanjut tentang hasil scan Anda.
          </p>
        </div>
      </div>
    </div>
  );
}
