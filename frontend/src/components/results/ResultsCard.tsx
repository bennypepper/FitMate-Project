"use client";

import React from "react";

interface ResultsCardProps {
  ingredients: any[];
  ocrBlocks?: any[];
  disclaimer?: string;
  onReset: () => void;
}

export default function ResultsCard({
  ingredients,
  ocrBlocks = [],
  disclaimer,
  onReset,
}: ResultsCardProps) {
  const toxicItems = ingredients.filter(
    (i) => i.is_toxic || i.category === "toxic" || i.category === "contraindicated"
  );
  const safeItems = ingredients.filter(
    (i) => !i.is_toxic && i.category === "safe"
  );
  const unknownItems = ingredients.filter((i) => i.category === "unknown");

  // Primary highlight item if toxic, otherwise first safe item
  const primaryToxic = toxicItems[0];

  // Generate WhatsApp prefilled message
  const generateWhatsAppMessage = () => {
    let msg = "Halo Apoteker FitMate, saya baru saja memindai label TCM dan menemukan hasil berikut:\n\n";
    if (toxicItems.length > 0) {
      msg += `⚠️ BAHAN BERISIKO (${toxicItems.length}):\n`;
      toxicItems.forEach((item, idx) => {
        const name = item.matched_mandarin || item.english_name || item.indonesian_name || item.detected_text;
        const desc = item.description ? ` (${item.description})` : "";
        msg += `${idx + 1}. ${name}${desc}\n`;
      });
      msg += "\nMohon konfirmasi dan rekomendasi keamanan untuk mengonsumsi produk ini.";
    } else {
      msg += `✅ BAHAN AMAN (${safeItems.length}):\n`;
      safeItems.forEach((item, idx) => {
        const name = item.matched_mandarin || item.english_name || item.indonesian_name || item.detected_text;
        msg += `${idx + 1}. ${name}\n`;
      });
      msg += "\nApakah ada petunjuk dosis atau anjuran minum yang tepat?";
    }
    return msg;
  };

  const handleOpenWhatsApp = () => {
    const text = encodeURIComponent(generateWhatsAppMessage());
    window.open(`https://wa.me/14155238886?text=${text}`, "_blank");
  };

  return (
    <div className="w-full max-w-[460px] mx-auto bg-card rounded-[28px] border border-line p-4 md:p-6 shadow-xl flex flex-col animate-in fade-in zoom-in-95 duration-300">
      {/* Screen Header */}
      <div className="flex items-center justify-between pb-3 border-b border-line mb-4">
        <button
          onClick={onReset}
          className="w-[34px] h-[34px] rounded-full bg-paper-deep text-ink hover:bg-paper transition flex items-center justify-center"
          title="Kembali ke Kamera"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <h2 className="font-serif font-bold text-[18px] text-ink">Hasil Pindai</h2>
        <div className="w-[34px] h-[34px]" />
      </div>

      {/* Hero Result Banner */}
      {toxicItems.length > 0 ? (
        <div className="bg-danger-tint border border-danger/30 rounded-[16px] p-4 mb-5">
          <div className="inline-flex items-center gap-1.5 bg-danger text-white text-[11px] font-semibold px-2.5 py-1 rounded-full mb-2.5">
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path d="M12 9v4M12 17h.01M10.3 3.9L2.5 17a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
            </svg>
            <span>{toxicItems.length} bahan berisiko ditemukan</span>
          </div>
          <h3 className="font-serif text-[17px] font-bold text-heritage-deep mb-1.5">
            {primaryToxic?.matched_mandarin
              ? `${primaryToxic.matched_mandarin} (${primaryToxic.indonesian_name || primaryToxic.english_name || primaryToxic.detected_text}) terdeteksi`
              : `${primaryToxic?.english_name || primaryToxic?.indonesian_name || primaryToxic?.detected_text} terdeteksi`}
          </h3>
          <p className="text-[12.5px] leading-relaxed text-ink">
            {primaryToxic?.description ||
              "Mengandung senyawa yang memiliki peringatan toksisitas atau kontraindikasi klinis. Tidak dianjurkan untuk dikonsumsi tanpa resep atau pengawasan apoteker berlisensi."}
          </p>
        </div>
      ) : (
        <div className="bg-trust-tint border border-trust/30 rounded-[16px] p-4 mb-5">
          <div className="inline-flex items-center gap-1.5 bg-trust text-white text-[11px] font-semibold px-2.5 py-1 rounded-full mb-2.5">
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>Semua bahan aman</span>
          </div>
          <h3 className="font-serif text-[17px] font-bold text-trust-deep mb-1.5">
            Tidak Ditemukan Bahan Berbahaya
          </h3>
          <p className="text-[12.5px] leading-relaxed text-ink">
            Semua bahan yang terdeteksi cocok dengan daftar herbal aman pada basis data apotek tervalidasi kami.
          </p>
        </div>
      )}

      {/* Ingredient Breakdown List */}
      <div className="mb-5">
        <div className="flex items-center justify-between mb-2.5">
          <h4 className="text-[12px] font-bold uppercase tracking-wider text-ink-soft">
            Rincian Komposisi Bahan ({ingredients.length})
          </h4>
          <span className="text-[11px] text-ink-faint">Rule-based lookup</span>
        </div>

        <div className="flex flex-col gap-2">
          {ingredients.map((item, idx) => {
            const isToxic =
              item.is_toxic || item.category === "toxic" || item.category === "contraindicated";
            const zh = item.matched_mandarin || item.detected_text;
            const sub =
              item.indonesian_name || item.english_name || item.latin_name || "Herbal Terverifikasi";

            return (
              <div
                key={idx}
                className={`flex items-center justify-between p-3 rounded-[12px] border transition-colors ${
                  isToxic
                    ? "bg-danger-tint border-danger/30"
                    : "bg-paper border-line"
                }`}
              >
                <div className="flex flex-col pr-2">
                  <span className="font-semibold text-[13.5px] text-ink">
                    {zh}
                  </span>
                  <span className="text-[11px] text-ink-soft mt-0.5">
                    {sub}
                  </span>
                </div>

                <div className="flex-shrink-0">
                  {isToxic ? (
                    <span className="inline-block text-[10.5px] font-bold px-2.5 py-1 rounded-full bg-danger text-white shadow-xs">
                      Berisiko
                    </span>
                  ) : item.category === "unknown" ? (
                    <span className="inline-block text-[10.5px] font-medium px-2 py-0.5 rounded-full bg-paper-deep text-ink-soft border border-line">
                      Perlu Review
                    </span>
                  ) : (
                    <span className="inline-block text-[10.5px] font-bold px-2.5 py-1 rounded-full bg-trust-tint text-trust-deep border border-trust/20">
                      Aman
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* WhatsApp Consultation Banner */}
      <button
        onClick={handleOpenWhatsApp}
        className="w-full bg-heritage hover:bg-heritage-deep text-white rounded-[16px] p-3.5 flex items-center gap-3 transition-colors shadow-sm text-left mb-3 group"
      >
        <div className="w-[38px] h-[38px] rounded-full bg-white/15 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12.04 2c-5.5 0-9.96 4.46-9.96 9.96 0 1.76.46 3.4 1.26 4.83L2 22l5.34-1.28a9.9 9.9 0 0 0 4.7 1.2h.01c5.5 0 9.96-4.46 9.96-9.96S17.54 2 12.04 2z" />
          </svg>
        </div>
        <div className="flex-1">
          <strong className="block text-[13px] font-semibold text-white">
            Lanjut konsultasi via WhatsApp
          </strong>
          <span className="block text-[11px] text-white/75 mt-0.5">
            Panduan berbasis aturan, bukan tebakan AI
          </span>
        </div>
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="text-white/60 group-hover:translate-x-0.5 transition-transform"
        >
          <path d="M9 18l6-6-6-6" />
        </svg>
      </button>

      {/* Scan Another Label Button */}
      <button
        onClick={onReset}
        className="w-full py-2.5 text-[12.5px] font-semibold text-ink-soft hover:text-ink transition flex items-center justify-center gap-1.5"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
        >
          <path d="M3 12a9 9 0 1 0 3-6.7" />
          <path d="M3 4v5h5" />
        </svg>
        Pindai Label Lain
      </button>

      {/* Medical Disclaimer */}
      {disclaimer && (
        <p className="text-[10px] text-ink-faint text-center mt-3 leading-relaxed border-t border-line/40 pt-2.5">
          {disclaimer}
        </p>
      )}
    </div>
  );
}
