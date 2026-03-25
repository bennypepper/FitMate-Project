"use client";

import { useState } from "react";
import CameraViewfinder from "@/components/scanner/CameraViewfinder";
import UploadFallback from "@/components/scanner/UploadFallback";
import ProcessingLoader from "@/components/scanner/ProcessingLoader";

export default function ScannerPage() {
  const [image, setImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleImageReady = (base64: string) => {
    setImage(base64);
    setIsProcessing(true);

    // Simulate API call for now (Phase 03-02 requirement)
    setTimeout(() => {
      setIsProcessing(false);
      // Results handling will be implemented in Phase 03-03
    }, 2000);
  };

  return (
    <main className="flex flex-col flex-1 items-center justify-center p-4 max-w-md mx-auto w-full relative min-h-[100dvh]">
      <h1 className="font-serif text-3xl font-bold text-primary mb-2 text-center tracking-tight">
        FitMate
      </h1>
      <h2 className="font-sans text-lg font-medium text-secondary mb-8 text-center uppercase tracking-widest">
        Apothecary Scanner
      </h2>
      
      <p className="font-sans text-on-surface text-center mb-8 leading-relaxed">
        Arahkan kamera ke komposisi TCM (huruf Mandarin) untuk melihat analisis keamanan.
      </p>

      {isProcessing && <ProcessingLoader />}

      <CameraViewfinder onCapture={handleImageReady} />
      <UploadFallback onImageReady={handleImageReady} />
    </main>
  );
}
