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
    <main className="flex flex-col flex-1 items-center justify-center p-4 max-w-md mx-auto w-full relative min-h-[100dvh]">
      {!results && (
        <>
          <h1 className="font-serif text-3xl font-bold text-primary mb-2 text-center tracking-tight">
            FitMate
          </h1>
          <h2 className="font-sans text-lg font-medium text-secondary mb-8 text-center uppercase tracking-widest">
            Apothecary Scanner
          </h2>
          
          <p className="font-sans text-on-surface text-center mb-8 leading-relaxed">
            Arahkan kamera ke komposisi TCM (huruf Mandarin) untuk melihat analisis keamanan.
          </p>

          <CameraViewfinder onCapture={handleImageReady} />
          <UploadFallback onImageReady={handleImageReady} />
        </>
      )}

      {isProcessing && <ProcessingLoader />}

      {networkError && !isProcessing && (
        <div className="bg-surface-container-low w-full rounded-xl p-6 shadow-ambient mb-4 outline outline-2 outline-error">
          <div className="flex flex-col items-center gap-4 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-on-surface font-sans font-medium">{networkError}</p>
            <button onClick={handleReset} className="mt-2 px-6 py-2 bg-primary text-on-primary font-bold rounded-lg shadow-sm transition active:scale-95">
              Coba Lagi
            </button>
          </div>
        </div>
      )}

      {results && !isProcessing && !networkError && (
        <ResultsCard ingredients={results.ingredients} onReset={handleReset} />
      )}
    </main>
  );
}
