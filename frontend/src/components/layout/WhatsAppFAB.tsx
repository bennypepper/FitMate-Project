"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { usePathname } from "next/navigation";

const WA_NUMBER = "6285161618852";
const WA_MESSAGE =
  "Halo FitMate! Saya ingin berkonsultasi mengenai keamanan bahan TCM yang saya pindai.";
const WA_URL = `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(WA_MESSAGE)}`;

// Bounce animation: 300ms start, 650ms duration → done at ~950ms
const BOUNCE_DELAY_MS = 300;
const BOUNCE_DURATION_MS = 650;
const BOUNCE_DONE_MS = BOUNCE_DELAY_MS + BOUNCE_DURATION_MS + 100; // +100ms safety buffer

const WaIcon = ({ size = 22 }: { size?: number }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    fill="currentColor"
    viewBox="0 0 16 16"
  >
    <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.9 7.9 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.9 7.9 0 0 0 13.6 2.326zM7.994 14.521a6.6 6.6 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.56 6.56 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592m3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.73.73 0 0 0-.529.247c-.182.198-.691.677-.691 1.654s.71 1.916.81 2.049c.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232" />
  </svg>
);

export default function WhatsAppFAB() {
  const pathname = usePathname();
  const [cardOpen, setCardOpen] = useState(false);
  const [nudgeOpen, setNudgeOpen] = useState(false);
  const [bounceReady, setBounceReady] = useState(false);
  const leaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  if (pathname?.startsWith("/admin")) return null;

  useEffect(() => {
    // Trigger bounce
    const bounceTimer = setTimeout(() => setBounceReady(true), BOUNCE_DELAY_MS);

    // Show nudge pill only AFTER bounce is fully done
    const nudgeShow = setTimeout(() => setNudgeOpen(true), BOUNCE_DONE_MS);
    const nudgeHide = setTimeout(() => setNudgeOpen(false), BOUNCE_DONE_MS + 4000);

    return () => {
      clearTimeout(bounceTimer);
      clearTimeout(nudgeShow);
      clearTimeout(nudgeHide);
    };
  }, []);

  // Hover with travel-grace so cursor can move from FAB → card
  const handleFabEnter = useCallback(() => {
    if (leaveTimer.current) clearTimeout(leaveTimer.current);
    setCardOpen(true);
    setNudgeOpen(false);
  }, []);

  const handleLeave = useCallback(() => {
    leaveTimer.current = setTimeout(() => setCardOpen(false), 180);
  }, []);

  const handleCardEnter = useCallback(() => {
    if (leaveTimer.current) clearTimeout(leaveTimer.current);
  }, []);

  // Mobile: tap FAB to toggle full card
  const handleFabClick = (e: React.MouseEvent) => {
    if (window.matchMedia("(hover: none)").matches) {
      e.preventDefault();
      setCardOpen((prev) => !prev);
      setNudgeOpen(false);
    }
  };

  return (
    <>
      <style>{`
        @keyframes fab-bounce-in {
          0%   { transform: translateY(-30px); opacity: 0; }
          55%  { transform: translateY(8px);   opacity: 1; }
          75%  { transform: translateY(-5px);  }
          90%  { transform: translateY(3px);   }
          100% { transform: translateY(0);     opacity: 1; }
        }
        .fab-bounce {
          animation: fab-bounce-in ${BOUNCE_DURATION_MS}ms cubic-bezier(0.22, 1, 0.36, 1) ${BOUNCE_DELAY_MS}ms both;
        }
      `}</style>

      {/* Fixed anchor — only the FAB circle is in flow; card + pill are absolute */}
      <div className="fixed bottom-6 right-5 z-50">
        <div className="relative">

          {/* ── Small nudge pill — absolute, above FAB ── */}
          <div
            className={`
              absolute bottom-full right-0 mb-3
              flex items-center gap-1.5
              bg-white border border-slate-100 rounded-full
              px-3 py-1.5 shadow-lg whitespace-nowrap
              transition-all duration-300 ease-out origin-bottom-right
              ${nudgeOpen
                ? "opacity-100 scale-100 translate-y-0 pointer-events-auto"
                : "opacity-0 scale-90 translate-y-2 pointer-events-none"
              }
            `}
          >
            <span className="text-[11px] font-semibold text-on-surface">
              Konsultasi TCM 🌿
            </span>
            <button
              onClick={() => setNudgeOpen(false)}
              className="text-on-surface-variant hover:text-on-surface transition-colors"
              aria-label="Tutup"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {/* ── Full consultation card — absolute, above FAB ── */}
          <div
            onMouseEnter={handleCardEnter}
            onMouseLeave={handleLeave}
            className={`
              absolute bottom-full right-0 mb-3
              w-64 bg-white rounded-2xl shadow-2xl border border-slate-100
              overflow-hidden origin-bottom-right
              transition-all duration-250 ease-out
              ${cardOpen
                ? "opacity-100 scale-100 translate-y-0 pointer-events-auto"
                : "opacity-0 scale-95 translate-y-3 pointer-events-none"
              }
            `}
          >
            {/* Header */}
            <div className="bg-[#25D366] px-4 py-3 flex items-center gap-2">
              <WaIcon size={18} />
              <span className="text-white text-sm font-bold tracking-wide">FitMate Chatbot</span>
              <button
                onClick={() => setCardOpen(false)}
                className="ml-auto text-white/80 hover:text-white transition-colors"
                aria-label="Tutup"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {/* Body */}
            <div className="px-4 py-3 flex flex-col gap-3">
              <div className="flex items-start gap-2">
                <div className="w-7 h-7 rounded-full bg-[#25D366] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <WaIcon size={14} />
                </div>
                <div className="bg-slate-50 rounded-2xl rounded-tl-sm px-3 py-2 text-xs text-on-surface leading-relaxed border border-slate-100">
                  Ada pertanyaan tentang bahan TCM yang baru Anda pindai? 🌿
                  <br />
                  <span className="text-on-surface-variant">
                    Konsultasikan langsung dengan chatbot kami.
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {["Cek Toksisitas", "Kontraindikasi", "Dosis Aman"].map((tag) => (
                  <span
                    key={tag}
                    className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-primary/8 text-primary border border-primary/15"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              <a
                href={WA_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-[#25D366] text-white text-xs font-bold tracking-wide shadow-sm hover:brightness-105 active:scale-95 transition-all duration-150"
              >
                <WaIcon size={14} />
                Mulai Konsultasi
              </a>

              <p className="text-[9px] text-on-surface-variant text-center leading-snug">
                Balasan otomatis • Bukan diagnosis medis
              </p>
            </div>
          </div>

          {/* ── FAB circle — hover trigger ── */}
          <div
            onMouseEnter={handleFabEnter}
            onMouseLeave={handleLeave}
          >
            <a
              href={WA_URL}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleFabClick}
              aria-label="Konsultasi via WhatsApp"
              className={`
                flex items-center justify-center
                w-14 h-14 rounded-full
                bg-[#25D366] text-white
                shadow-[0_4px_20px_rgba(37,211,102,0.45)]
                transition-transform duration-150
                hover:scale-110 active:scale-95
                ${bounceReady ? "fab-bounce" : "opacity-0"}
              `}
            >
              <WaIcon size={28} />
            </a>
          </div>

        </div>
      </div>
    </>
  );
}
