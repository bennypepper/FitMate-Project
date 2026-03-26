import React from "react";
import ToxicityWarning from "./ToxicityWarning";
import IngredientList from "./IngredientList";

interface ResultsCardProps {
  ingredients: any[];
  onReset: () => void;
}

export default function ResultsCard({ ingredients, onReset }: ResultsCardProps) {
  const toxicItems = ingredients.filter(i => i.is_toxic);

  return (
    <div className="animate-in fade-in zoom-in duration-500 w-full mb-32">
      <div className="mb-12 text-left">
        <h2 className="font-headline text-5xl font-bold text-primary tracking-tight mb-2">Hasil Pemindaian</h2>
        <p className="font-body text-on-surface-variant text-lg">Analisis terperinci dari profil suplemen TCM Anda.</p>
      </div>

      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-7 space-y-8">
          <ToxicityWarning ingredients={ingredients} />
          <IngredientList ingredients={ingredients} />
        </div>

        <div className="lg:col-span-5 space-y-6 lg:sticky lg:top-24">
          <div className="aspect-square w-full rounded-2xl overflow-hidden relative group shadow-lg">
            <div className="absolute inset-0 bg-accent/20" />
            <div className="absolute inset-0 bg-light/30 backdrop-blur-[20px] flex flex-col items-center justify-center p-8 text-center border border-light/50 rounded-2xl">
              <div className="w-16 h-16 border-2 border-primary rounded-full flex items-center justify-center mb-4 bg-white/50">
                <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>verified</span>
              </div>
              <h6 className="font-headline text-2xl font-bold text-dark mb-2">Verifikasi Klinis</h6>
              <p className="font-body text-sm text-on-surface-variant">AI mencocokkan molekul yang dipindai dengan Database Keamanan TCM v1.0</p>
            </div>
          </div>

          <div className="bg-background shadow-md p-8 rounded-2xl border border-light/50">
            <h6 className="font-headline text-xl font-bold text-primary mb-4">Tindakan yang Disarankan</h6>
            <ul className="space-y-4">
              {toxicItems.length > 0 ? (
                <>
                  <li className="flex gap-4">
                    <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>do_not_disturb_on</span>
                    <p className="font-body text-sm text-on-surface">Segera hentikan konsumsi dari produk ini.</p>
                  </li>
                  <li className="flex gap-4">
                    <span className="material-symbols-outlined text-primary">clinical_notes</span>
                    <p className="font-body text-sm text-on-surface">Simpan info digital ini untuk penyedia layanan kesehatan Anda.</p>
                  </li>
                </>
              ) : (
                <li className="flex gap-4">
                  <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                  <p className="font-body text-sm text-on-surface">Tidak ada bahan berbahaya yang terdeteksi secara otomatis.</p>
                </li>
              )}
              <li className="flex gap-4 pt-4 border-t border-light/30">
                <span className="material-symbols-outlined text-secondary">restart_alt</span>
                <button className="font-body text-sm text-secondary hover:text-primary underline font-bold text-left transition" onClick={onReset}>
                  Pindai Label Lain
                </button>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* WhatsApp Button - Always present */}
      <div className="fixed bottom-24 left-0 right-0 px-6 flex justify-center pointer-events-none z-10 w-full">
        <a
          href={`https://wa.me/6285161618852?text=${encodeURIComponent(
            toxicItems.length > 0 
              ? "Halo FitMate! Saya baru scan produk TCM dan ditemukan bahan berbahaya: " + toxicItems.map((item) => item.indonesian_name || item.mandarin_name || item.matched_mandarin).join(", ") + ". Bisa bantu jelaskan risikonya?"
              : "Halo FitMate! Saya ingin berkonsultasi mengenai suplemen TCM ini."
          )}`}
          target="_blank"
          rel="noopener noreferrer"
          className="pointer-events-auto bg-accent text-dark font-body font-bold text-lg px-8 py-4 md:px-12 md:py-5 rounded-xl shadow-2xl flex items-center gap-4 transition-transform active:scale-95 duration-150 border-b-4 border-dark/20 hover:brightness-105"
        >
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>chat</span>
          Konsultasi via WhatsApp
        </a>
      </div>
    </div>
  );
}
