"use client";

import { useEffect, useRef, useState } from "react";

interface CameraViewfinderProps {
  onCapture: (base64Image: string) => void;
  uploadFallbackNode: React.ReactNode;
}

export default function CameraViewfinder({ onCapture, uploadFallbackNode }: CameraViewfinderProps) {
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
        setError("Kamera tidak dapat diakses.");
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
    <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-large items-start">
      {/* Central Camera Feed Area */}
      <div className="lg:col-span-8 relative group">
        <div className="aspect-[4/3] md:aspect-video rounded-card overflow-hidden bg-black shadow-xl relative">
          {error ? (
            <div className="w-full h-full flex items-center justify-center text-white bg-dark/80 p-4 font-body">{error}</div>
          ) : (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover opacity-80"
            />
          )}

          {/* Scanner Overlays */}
          {!error && (
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute inset-0 border-[30px] md:border-[50px] border-dark/40 glass-blur"></div>
              <div className="absolute inset-[30px] md:inset-[50px] flex items-center justify-center">
                <div className="absolute top-0 left-0 w-10 h-10 border-t-4 border-l-4 border-accent rounded-tl-lg"></div>
                <div className="absolute top-0 right-0 w-10 h-10 border-t-4 border-r-4 border-accent rounded-tr-lg"></div>
                <div className="absolute bottom-0 left-0 w-10 h-10 border-b-4 border-l-4 border-accent rounded-bl-lg"></div>
                <div className="absolute bottom-0 right-0 w-10 h-10 border-b-4 border-r-4 border-accent rounded-br-lg"></div>

                <div className="absolute top-6 px-4 py-1.5 bg-primary/90 text-white text-[10px] tracking-widest uppercase font-bold rounded-badge font-chinese">
                  FOKUS PADA TEKS HANZI
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Controls */}
      <div className="lg:col-span-4 flex flex-col gap-large w-full">
        {!error && (
          <button
            onClick={handleCapture}
            className="w-full bg-accent text-dark py-8 rounded-button flex flex-col items-center justify-center gap-2 shadow-md hover:brightness-105 active:scale-95 transition-all"
          >
            <span className="material-symbols-outlined text-4xl" style={{ fontVariationSettings: "'FILL' 1" }}>
              photo_camera
            </span>
            <span className="font-bold tracking-widest text-sm">AMBIL GAMBAR</span>
          </button>
        )}

        {/* Gallery Section built from UI template */}
        <div className="bg-light/10 p-6 rounded-card border border-light/30">
          <div className="flex items-center justify-between mb-4">
            <span className="font-headline text-lg text-dark font-bold">Unggah Galeri</span>
            <span className="material-symbols-outlined text-secondary">image</span>
          </div>
          <p className="text-sm text-on-surface-variant mb-6">Sudah punya foto labelnya? Unggah di sini untuk analisis instan.</p>
          {uploadFallbackNode}
        </div>

        {/* Safety Protocol Card */}
        <div className="bg-primary/5 p-6 rounded-card border-l-4 border-primary">
          <div className="flex gap-4 items-start">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
              verified_user
            </span>
            <div>
              <h4 className="font-headline text-md text-dark font-bold">Protokol Keamanan</h4>
              <p className="text-xs text-on-surface-variant leading-relaxed mt-1">
                AI kami mengidentifikasi komponen berbahaya dalam TCM. Pastikan teks terlihat jelas untuk akurasi maksimal.
              </p>
            </div>
          </div>
        </div>
      </div>

      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}
