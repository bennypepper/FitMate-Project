"use client";

import { useEffect, useRef, useState } from "react";

interface CameraViewfinderProps {
  onCapture: (base64Image: string) => void;
  onReset?: () => void;
}

export default function CameraViewfinder({ onCapture, onReset }: CameraViewfinderProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment");

  useEffect(() => {
    let currentStream: MediaStream | null = null;

    async function startCamera() {
      try {
        setError(null);
        if (currentStream) {
          currentStream.getTracks().forEach((t) => t.stop());
        }
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: facingMode,
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        });
        currentStream = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err: unknown) {
        console.warn("[Camera] Camera access warning:", err);
        setError("Kamera tidak dapat diakses atau izin ditolak. Silakan gunakan tombol galeri/file.");
      }
    }

    startCamera();

    return () => {
      if (currentStream) {
        currentStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [facingMode]);

  const handleCapture = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const base64 = canvas.toDataURL("image/jpeg", 0.9);
        onCapture(base64);
      }
    } else if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        onCapture(reader.result);
      }
    };
    reader.readAsDataURL(file);
  };

  const toggleCamera = () => {
    setFacingMode((prev) => (prev === "environment" ? "user" : "environment"));
  };

  return (
    <div className="w-full max-w-full md:max-w-4xl mx-auto bg-card rounded-[22px] border border-line p-3 sm:p-5 md:p-6 shadow-xl flex flex-col animate-in fade-in duration-200">
      {/* Hidden File Input & Canvas */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileUpload}
      />
      <canvas ref={canvasRef} className="hidden" />

      {/* Screen Header Bar */}
      <div className="flex items-center justify-between gap-3 mb-3 px-1">
        <div className="flex items-center gap-2.5">
          {onReset && (
            <button
              onClick={onReset}
              className="px-3 py-1.5 rounded-[10px] bg-paper-deep hover:bg-line text-ink text-[12.5px] font-medium transition cursor-pointer flex items-center gap-1.5"
              title="Kembali ke Halaman Utama"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M15 18l-6-6 6-6" />
              </svg>
              <span>Kembali</span>
            </button>
          )}

          {/* Live Status Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-trust-tint text-trust-deep text-[11.5px] font-semibold border border-trust/20">
            <span className="w-2 h-2 rounded-full bg-trust animate-pulse" />
            <span>Kamera Pemindai Aktif</span>
          </div>
        </div>

        {/* Quick Actions (Switch Camera / Upload fallback) */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleCamera}
            className="px-3 py-1.5 rounded-[10px] bg-paper-deep hover:bg-line text-ink-soft hover:text-ink text-[12px] font-medium transition cursor-pointer flex items-center gap-1.5"
            title="Putar Kamera / Ganti Input"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 10c0-4.418-3.582-8-8-8s-8 3.582-8 8c0 2.21 0.895 4.21 2.343 5.657L4 18h5v-5l-1.657 1.657A5.98 5.98 0 0 1 6 10c0-3.314 2.686-6 6-6s6 2.686 6 6c0 1.657-0.672 3.157-1.757 4.243l1.414 1.414A7.96 7.96 0 0 0 20 10z" />
            </svg>
            <span className="hidden sm:inline">Ganti Kamera</span>
          </button>

          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1.5 rounded-[10px] bg-paper-deep hover:bg-line text-ink-soft hover:text-ink text-[12px] font-medium transition cursor-pointer flex items-center gap-1.5"
            title="Unggah Foto dari Berkas Komputer"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="3" />
              <circle cx="9" cy="9" r="1.6" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
            <span className="hidden sm:inline">Pilih File</span>
          </button>
        </div>
      </div>

      {/* Adaptive Viewfinder Frame (Landscape on Desktop, Natural Portrait on Phone) */}
      <div className="relative w-full aspect-[4/5] sm:aspect-[16/10] md:aspect-[16/9] max-h-[62vh] rounded-[18px] overflow-hidden bg-gradient-to-b from-[#1C1814] via-[#120F0D] to-[#0A0908] flex items-center justify-center shadow-inner border border-white/5">
        {/* Subtle Vignette Background Texture */}
        <div
          className="absolute inset-0 opacity-30 pointer-events-none"
          style={{
            backgroundImage:
              "repeating-linear-gradient(100deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 60px)",
          }}
        />

        {error ? (
          <div className="p-8 text-center text-white/90 z-10 max-w-md">
            <svg
              className="w-12 h-12 mx-auto mb-3 text-amber"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <p className="text-xs sm:text-sm leading-relaxed mb-4 text-paper-deep">{error}</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-5 py-2.5 bg-trust hover:bg-trust-deep text-white text-xs sm:text-sm font-semibold rounded-[10px] shadow transition cursor-pointer"
            >
              Pilih Foto dari Galeri / Berkas
            </button>
          </div>
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
        )}

        {/* Viewfinder Target Overlays */}
        {!error && (
          <>
            {/* Top Prompt Overlay */}
            <div className="absolute top-4 inset-x-0 mx-auto max-w-max px-4 py-1.5 rounded-full bg-black/75 backdrop-blur-md border border-white/20 text-white text-[11.5px] sm:text-[12.5px] font-medium shadow-md pointer-events-none text-center">
              Posisikan teks komposisi / aksara Hanzi di dalam bingkai target
            </div>

            {/* Target Bracket Frame (Scales adaptively: wider on desktop, compact on mobile) */}
            <div className="absolute inset-x-[12%] sm:inset-x-[20%] md:inset-x-[26%] top-[14%] sm:top-[16%] bottom-[16%] sm:bottom-[18%] pointer-events-none">
              {/* Corner TL */}
              <div className="absolute top-0 left-0 w-8 h-8 sm:w-10 sm:h-10 border-t-[3px] border-l-[3px] border-trust rounded-tl-[12px] shadow-[0_0_10px_rgba(33,122,96,0.5)]" />
              {/* Corner TR */}
              <div className="absolute top-0 right-0 w-8 h-8 sm:w-10 sm:h-10 border-t-[3px] border-r-[3px] border-trust rounded-tr-[12px] shadow-[0_0_10px_rgba(33,122,96,0.5)]" />
              {/* Corner BL */}
              <div className="absolute bottom-0 left-0 w-8 h-8 sm:w-10 sm:h-10 border-b-[3px] border-l-[3px] border-trust rounded-bl-[12px] shadow-[0_0_10px_rgba(33,122,96,0.5)]" />
              {/* Corner BR */}
              <div className="absolute bottom-0 right-0 w-8 h-8 sm:w-10 sm:h-10 border-b-[3px] border-r-[3px] border-trust rounded-br-[12px] shadow-[0_0_10px_rgba(33,122,96,0.5)]" />

              {/* Animated Laser Scanning Line */}
              <div className="absolute inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-[#60C4AB] to-transparent animate-scan-sweep shadow-[0_0_12px_#60C4AB]" />
            </div>

            {/* Bottom Tip Overlay */}
            <div className="absolute bottom-4 inset-x-0 mx-auto max-w-max px-3.5 py-1 rounded-full bg-black/50 backdrop-blur-sm text-paper/80 text-[11px] pointer-events-none hidden sm:flex items-center gap-1.5">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="text-[#60C4AB]">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
              <span>Pastikan pencahayaan cukup dan teks obat terlihat tajam</span>
            </div>
          </>
        )}
      </div>

      {/* Bottom Controls Bar (Ergonomic Desktop & Mobile) */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 md:pt-5 border-t border-line/60 mt-4">
        {/* Left note */}
        <div className="flex items-center gap-2 text-[12px] text-ink-soft order-2 sm:order-1">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" className="text-trust flex-shrink-0">
            <path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5z" />
          </svg>
          <span>Dicocokkan langsung ke 500 basis data keamanan TCM</span>
        </div>

        {/* Primary Shutter Action */}
        <div className="flex items-center gap-3 order-1 sm:order-2 w-full sm:w-auto justify-center">
          <button
            onClick={handleCapture}
            className="w-full sm:w-auto px-7 py-3 rounded-[14px] bg-trust hover:bg-trust-deep text-white text-[13.5px] font-bold shadow-[0_8px_20px_-6px_rgba(19,75,61,0.55)] transition-all hover:scale-[1.02] active:scale-95 cursor-pointer flex items-center justify-center gap-2.5"
            title="Ambil Foto Label & Analisis"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <span>Ambil Foto Label &amp; Analisis</span>
          </button>
        </div>
      </div>
    </div>
  );
}
