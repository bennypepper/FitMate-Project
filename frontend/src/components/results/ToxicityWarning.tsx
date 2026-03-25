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
            <p className="font-sans font-bold text-lg mb-1">{item.indonesian_name || item.mandarin_name || item.matched_mandarin}</p>
            <p className="text-sm opacity-90 font-sans"><strong>Organ Target:</strong> {item.target_organ || "Tidak diketahui"}</p>
            <p className="text-sm opacity-90 mt-1 font-sans">{item.severity_warning || item.description || "Komponen berisiko tinggi ditemukan."}</p>
          </div>
        ))}
      </div>
      {toxicItems.length > 0 && (
        <a
          href={`https://wa.me/6285161618852?text=${encodeURIComponent(
            "Halo FitMate! Saya baru scan produk TCM dan ditemukan bahan berbahaya: " +
              toxicItems
                .map(
                  (item) =>
                    item.indonesian_name || item.mandarin_name || item.matched_mandarin
                )
                .join(", ") +
              ". Bisa bantu jelaskan risikonya?"
          )}`}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full bg-white text-[#930014] rounded-xl flex items-center justify-center p-3 mt-4 text-center font-bold shadow-sm transition active:scale-95 hover:bg-white/90"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 mr-2 fill-[#25D366]"
            viewBox="0 0 24 24"
          >
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
          </svg>
          Tanya di WhatsApp
        </a>
      )}
    </div>
  );
}
