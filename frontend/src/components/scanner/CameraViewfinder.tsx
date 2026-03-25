"use client";

import { useEffect, useRef, useState } from "react";

interface CameraViewfinderProps {
  onCapture: (base64Image: string) => void;
}

export default function CameraViewfinder({ onCapture }: CameraViewfinderProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let currentStream: MediaStream | null = null;

    async function setupCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        });
        currentStream = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err: any) {
        setError("Kamera tidak dapat diakses. Mohon izinkan akses kamera atau gunakan unggah foto dari galeri.");
      }
    }

    setupCamera();

    return () => {
      if (currentStream) {
        currentStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const handleCapture = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const base64 = canvas.toDataURL("image/jpeg");
        onCapture(base64);
      }
    }
  };

  return (
    <div className="flex flex-col items-center gap-4 w-full">
      <div className="relative w-full aspect-[3/4] bg-surface-container-high rounded-xl overflow-hidden shadow-ambient flex items-center justify-center">
        {error ? (
          <p className="text-error text-center px-4 font-sans text-sm">{error}</p>
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="absolute inset-0 w-full h-full object-cover"
          />
        )}
      </div>
      
      {!error && (
        <button
          onClick={handleCapture}
          className="bg-tertiary-container text-on-tertiary-fixed font-sans font-medium px-8 py-3 w-full rounded-md shadow-inner transition-transform active:scale-95"
        >
          Ambil Foto Label
        </button>
      )}
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}
