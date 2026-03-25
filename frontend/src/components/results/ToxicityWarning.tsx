import React from "react";

interface ToxicityWarningProps {
  ingredients: any[];
}

export default function ToxicityWarning({ ingredients }: ToxicityWarningProps) {
  if (!ingredients) return null;
  const toxicItems = ingredients.filter((item) => item.is_toxic);

  if (toxicItems.length === 0) {
    return (
      <div className="bg-surface-container-low w-full rounded-xl p-4 shadow-ambient mb-4 outline outline-2 outline-surface-container-highest">
        <p className="text-on-surface font-sans text-center font-medium">
          Tidak ditemukan komponen sangat berbahaya atau kontraindikasi berat.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-primary-container text-surface-container-lowest w-full rounded-xl p-5 shadow-[0_8px_32px_-10px_rgba(147,0,20,0.4)] mb-6">
      <div className="flex items-center gap-3 mb-4">
        <svg xmlns="http://www.w3.org/2000/0.svg" className="h-8 w-8 text-tertiary-container" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="font-serif text-2xl font-bold tracking-tight">PERINGATAN KLINIS</h3>
      </div>
      <div className="flex flex-col gap-3">
        {toxicItems.map((item, idx) => (
          <div key={idx} className="bg-black/10 rounded-lg p-3 border border-white/10">
            <p className="font-sans font-bold text-lg mb-1">{item.indonesian_name || item.mandarin_name}</p>
            <p className="text-sm opacity-90 font-sans"><strong>Organ Target:</strong> {item.target_organ || "Tidak diketahui"}</p>
            <p className="text-sm opacity-90 mt-1 font-sans">{item.severity_warning || item.description || "Komponen berisiko tinggi ditemukan."}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
