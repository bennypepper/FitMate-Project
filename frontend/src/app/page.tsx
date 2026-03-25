"use client";

import { useState } from "react";
import CameraViewfinder from "@/components/scanner/CameraViewfinder";
import UploadFallback from "@/components/scanner/UploadFallback";
import ProcessingLoader from "@/components/scanner/ProcessingLoader";
import ResultsCard from "@/components/results/ResultsCard";

export default function ScannerPage() {
  const [image, setImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<any | null>(null);
  const [networkError, setNetworkError] = useState<string | null>(null);

  const handleImageReady = async (base64: string) => {
    setImage(base64);
    setIsProcessing(true);
    setResults(null);

    try {
      // Convert base64 to Blob
      const resMsg = await fetch(base64);
      const blob = await resMsg.blob();

      const formData = new FormData();
      formData.append("file", blob, "scan.jpg");

      const response = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1/analyze/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("API request failed");
      }

      const data = await response.json();
      // Backend returns: { status, ocr_blocks, safety_analysis: {toxic, contraindicated, safe, unknown}, disclaimer }
      const sa = data.safety_analysis || {};
      const allIngredients = [
        ...(sa.toxic || []).map((i: any) => ({ ...i, category: "toxic", is_toxic: true })),
        ...(sa.contraindicated || []).map((i: any) => ({ ...i, category: "contraindicated", is_toxic: true })),
        ...(sa.safe || []).map((i: any) => ({ ...i, category: "safe", is_toxic: false })),
        ...(sa.unknown || []).map((i: any) => ({ ...i, category: "unknown", is_toxic: false })),
      ];
      setResults({
        ingredients: allIngredients,
        disclaimer: data.disclaimer || "",
        ocr_blocks: data.ocr_blocks || [],
      });
    } catch (error) {
      console.error(error);
      if (!navigator.onLine) {
        setNetworkError("Tidak ada koneksi internet atau server tidak dapat dijangkau. Pastikan Anda terhubung ke internet untuk menggunakan fitur scanning.");
      } else {
        setNetworkError("Server tidak dapat dijangkau. Coba lagi dalam beberapa saat.");
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setImage(null);
    setResults(null);
    setNetworkError(null);
  };

  return (
    <main className="flex-grow flex flex-col items-center justify-center p-large md:p-12 max-w-5xl mx-auto w-full mb-24">
      {/* Header Section */}
      <div className="w-full text-left mb-10">
        <h1 className="font-headline text-4xl md:text-5xl text-dark font-bold leading-tight mb-4">
          Pindai Label Komposisi <br />TCM Anda
        </h1>
        <p className="font-body text-on-surface-variant text-lg max-w-2xl">
          Pastikan keamanan dan efektivitas dengan memverifikasi bahan-bahan terhadap basis data apotek modern kami.
        </p>
      </div>

      {isProcessing && <ProcessingLoader />}

      {!results && !isProcessing && (
        <CameraViewfinder 
          onCapture={handleImageReady} 
          uploadFallbackNode={<UploadFallback onImageReady={handleImageReady} />} 
        />
      )}

      {networkError && !isProcessing && (
        <div className="bg-primary/5 w-full rounded-card p-6 border-l-4 border-error mt-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <span className="material-symbols-outlined text-4xl text-error">wifi_off</span>
            <p className="text-dark font-body font-medium">{networkError}</p>
            <button onClick={handleReset} className="mt-2 px-6 py-2 bg-accent text-dark font-bold rounded-button shadow-sm transition active:scale-95">
              Coba Lagi
            </button>
          </div>
        </div>
      )}

      {results && !isProcessing && !networkError && (
        <div className="w-full mt-4">
          <ResultsCard ingredients={results.ingredients} onReset={handleReset} />
        </div>
      )}

      {/* Recent Scans Section (Placeholder) */}
      {!results && !isProcessing && (
        <div className="w-full mt-16">
          <div className="flex justify-between items-end mb-8">
            <h3 className="font-headline text-2xl text-dark font-bold">Pencarian Terbaru</h3>
            <a className="text-sm font-bold text-secondary hover:text-primary underline underline-offset-4 uppercase tracking-tight" href="#">
              Lihat Semua Riwayat
            </a>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Card 1 */}
            <div className="bg-light/5 aspect-square rounded-card overflow-hidden relative group cursor-pointer border border-light/20">
              <div className="absolute inset-0 bg-dark/10" />
              <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-dark/90 to-transparent">
                <p className="text-white text-xs font-bold uppercase tracking-wider">Lianhua Qingwen</p>
                <p className="text-white/70 text-[10px]">Terverifikasi 2 jam lalu</p>
              </div>
            </div>
            {/* Empty State */}
            <div className="border-2 border-dashed border-light/30 aspect-square rounded-card flex flex-col items-center justify-center gap-2 group hover:bg-light/5 transition-colors cursor-pointer">
              <span className="material-symbols-outlined text-light text-3xl">add_a_photo</span>
              <span className="text-[10px] font-bold text-light uppercase tracking-widest">Pindai Baru</span>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
