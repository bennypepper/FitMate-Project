import React from "react";

interface ToxicityWarningProps {
  ingredients: any[];
}

export default function ToxicityWarning({ ingredients }: ToxicityWarningProps) {
  if (!ingredients) return null;
  const toxicItems = ingredients.filter((item) => item.is_toxic);

  if (toxicItems.length === 0) {
    return null;
  }

  return (
    <>
      {/* Toxicity Warning Header */}
      <div className="bg-error-container rounded-xl p-8 border-l-8 border-primary relative overflow-hidden shadow-sm">
        <div className="absolute top-0 right-0 p-4 opacity-10">
          <span className="material-symbols-outlined text-9xl">warning</span>
        </div>
        <div className="relative z-10">
          <h3 className="font-headline text-3xl font-bold text-primary mb-2 uppercase tracking-wide">
            PERINGATAN TOKSISITAS TERDETEKSI
          </h3>
          <p className="font-body text-dark text-lg font-medium">
            Potensi bahaya klinis ditemukan dalam sampel saat ini.
          </p>
        </div>
      </div>

      {/* Critical Ingredient Cards */}
      <div className="space-y-6">
        {toxicItems.map((item, idx) => (
          <div key={idx} className="bg-white rounded-xl p-8 border border-light/50 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div className="flex-1">
                <span className="font-body text-xs font-bold uppercase tracking-widest text-primary block mb-2">
                  BAHAN KRITIS
                </span>
                <h4 className="font-headline text-4xl text-on-surface italic">
                  {item.indonesian_name || item.mandarin_name || item.matched_mandarin}
                </h4>
              </div>
              <div className="bg-dark px-6 py-3 rounded-xl flex items-center gap-3 shadow-lg shadow-primary/20">
                <span className="material-symbols-outlined text-white" style={{ fontVariationSettings: "'FILL' 1" }}>
                  heart_broken
                </span>
                <span className="font-body text-white font-bold uppercase text-sm tracking-tight">
                  {item.target_organ ? `RISIKO ${item.target_organ}` : "RISIKO KLINIS"}
                </span>
              </div>
            </div>

            <div className="mt-8 pt-8 border-t border-light/30">
              <p className="font-body text-on-surface-variant leading-relaxed text-lg">
                {item.severity_warning || item.description || "Terdapat temuan toksisitas atau kontraindikasi tinggi yang berisiko klinis. Konsultasi medis segera disarankan sebelum konsumsi lebih lanjut."}
              </p>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
