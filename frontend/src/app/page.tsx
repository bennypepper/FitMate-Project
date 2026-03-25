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

      const response = await fetch("http://localhost:8000/api/v1/analyze/", {
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
      alert("Gagal memproses gambar. Pastikan server lokal berjalan.");
      // For demo fallback if backend is down
      setResults({
        ingredients: [],
        disclaimer: "INFORMASI INI HANYA UNTUK TUJUAN EDUKASI",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setImage(null);
    setResults(null);
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

      {results && !isProcessing && (
        <ResultsCard ingredients={results.ingredients} onReset={handleReset} />
      )}
    </main>
  );
}
