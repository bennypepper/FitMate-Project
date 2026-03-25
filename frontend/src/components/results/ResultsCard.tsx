import React from "react";
import ToxicityWarning from "./ToxicityWarning";
import IngredientList from "./IngredientList";

interface ResultsCardProps {
  ingredients: any[];
  onReset: () => void;
}

export default function ResultsCard({ ingredients, onReset }: ResultsCardProps) {
  return (
    <div className="w-full flex flex-col items-center animate-in fade-in zoom-in duration-500 pb-8 mt-4">
      <h2 className="font-serif text-3xl font-bold text-on-surface mb-2 tracking-tight text-center">
        Hasil Analisis
      </h2>
      <p className="font-sans text-on-surface/80 text-center mb-8">
        Komposisi terdeteksi dari label produk.
      </p>

      <ToxicityWarning ingredients={ingredients} />
      
      <h3 className="font-sans font-medium text-lg text-on-surface mb-4 w-full text-left">Komposisi:</h3>
      <IngredientList ingredients={ingredients} />

      <p className="font-sans text-xs text-on-surface/50 text-center mt-6 px-4 border-t border-surface-container-high pt-6 leading-relaxed">
        INFORMASI INI HANYA UNTUK TUJUAN EDUKASI DAN BUKAN PENGGANTI SARAN MEDIS PROFESIONAL. KONSULTASIKAN DENGAN DOKTER ATAU APOTEKER.
      </p>

      <button
        onClick={onReset}
        className="mt-8 bg-surface-container-highest text-on-surface font-sans font-medium px-8 py-3 w-full rounded-md shadow-ambient transition-transform active:scale-95"
      >
        Pindai Label Lain
      </button>
    </div>
  );
}
