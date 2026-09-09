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
  const [streamActive, setStreamActive] = useState(false);

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
          setStreamActive(true);
        }
      } catch (err: any) {
        console.warn("[Camera] Camera access warning:", err);
        setError("Kamera tidak dapat diakses atau izin ditolak. Silakan gunakan tombol galeri/file.");
        setStreamActive(false);
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
    <div className="w-full max-w-[360px] mx-auto bg-card rounded-[28px] border border-line p-3 shadow-xl overflow-hidden flex flex-col">
      {/* Hidden File Input & Canvas */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileUpload}
      />
      <canvas ref={canvasRef} className="hidden" />

      {/* Screen Header */}
      <div className="flex items-center justify-between px-2 py-2 mb-1">
        <button
          onClick={onReset}
          className="w-[34px] height-[34px] p-2 rounded-full bg-paper-deep text-ink hover:bg-paper transition flex items-center justify-center"
          title="Kembali"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <div className="font-serif font-semibold text-[16px] text-heritage tracking-wide">
          FitMate
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-[34px] height-[34px] p-2 rounded-full bg-paper-deep text-ink-soft hover:text-ink transition flex items-center justify-center"
          title="Unggah Foto"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 12a9 9 0 1 0 3-6.7" />
            <path d="M3 4v5h5" />
            <path d="M12 7v5l3 3" />
          </svg>
        </button>
      </div>

      {/* Camera Viewfinder */}
      <div className="relative w-full aspect-[3/4] rounded-[22px] overflow-hidden bg-gradient-to-b from-[#2C2620] via-[#16130F] to-[#0E0C0A] flex items-center justify-center">
        {/* Background Texture */}
        <div
          className="absolute inset-0 opacity-40 pointer-events-none"
          style={{
            backgroundImage:
              "repeating-linear-gradient(100deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 60px)",
          }}
        />

        {error ? (
          <div className="p-6 text-center text-white/90 z-10">
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
            <p className="text-xs leading-relaxed mb-4">{error}</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-trust hover:bg-trust-deep text-white text-xs font-semibold rounded-lg shadow"
            >
              Pilih Foto dari Galeri
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
            <div className="absolute top-4 left-0 right-0 text-center px-4 text-paper/80 text-[11.5px] font-medium leading-tight drop-shadow">
              Posisikan teks Hanzi di label rata di dalam bingkai
            </div>

            {/* Target Bracket Frame */}
            <div className="absolute inset-x-[12%] top-[28%] bottom-[28%] pointer-events-none">
              {/* Corner TL */}
              <div className="absolute top-0 left-0 w-6 h-6 border-t-[2.5px] border-l-[2.5px] border-trust rounded-tl-[8px]" />
              {/* Corner TR */}
              <div className="absolute top-0 right-0 w-6 h-6 border-t-[2.5px] border-r-[2.5px] border-trust rounded-tr-[8px]" />
              {/* Corner BL */}
              <div className="absolute bottom-0 left-0 w-6 h-6 border-b-[2.5px] border-l-[2.5px] border-trust rounded-bl-[8px]" />
              {/* Corner BR */}
              <div className="absolute bottom-0 right-0 w-6 h-6 border-b-[2.5px] border-r-[2.5px] border-trust rounded-br-[8px]" />

              {/* Animated Laser Scanning Line */}
              <div className="absolute inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-[#60C4AB] to-transparent animate-scan-sweep shadow-[0_0_8px_#60C4AB]" />
            </div>

            <div className="absolute bottom-3 left-0 right-0 text-center text-paper/60 text-[11px]">
              Pencahayaan cukup — siap memindai
            </div>
          </>
        )}
      </div>

      {/* Bottom Controls (Thumb Zone) */}
      <div className="flex items-center justify-center gap-7 pt-4 pb-2">
        {/* Gallery / File Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-[46px] h-[46px] rounded-[14px] bg-paper-deep border border-line flex items-center justify-center text-ink-soft hover:text-ink active:scale-95 transition"
          title="Buka Galeri"
        >
          <svg
            width="19"
            height="19"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <rect x="3" y="3" width="18" height="18" rx="3" />
            <circle cx="9" cy="9" r="1.6" />
            <path d="M21 15l-5-5L5 21" />
          </svg>
        </button>

        {/* Shutter Capture Button */}
        <button
          onClick={handleCapture}
          className="w-[68px] h-[68px] rounded-full bg-trust border-[4px] border-trust-tint shadow-[0_8px_20px_-6px_rgba(19,75,61,0.55)] flex items-center justify-center text-white active:scale-95 transition hover:brightness-105"
          title="Ambil Foto"
        >
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
            <circle cx="12" cy="13" r="4" />
          </svg>
        </button>

        {/* Camera Switch / Flip Button */}
        <button
          onClick={toggleCamera}
          className="w-[46px] h-[46px] rounded-[14px] bg-paper-deep border border-line flex items-center justify-center text-ink-soft hover:text-ink active:scale-95 transition"
          title="Putar Kamera"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20 10c0-4.418-3.582-8-8-8s-8 3.582-8 8c0 2.21 0.895 4.21 2.343 5.657L4 18h5v-5l-1.657 1.657A5.98 5.98 0 0 1 6 10c0-3.314 2.686-6 6-6s6 2.686 6 6c0 1.657-0.672 3.157-1.757 4.243l1.414 1.414A7.96 7.96 0 0 0 20 10z" />
          </svg>
        </button>
      </div>

      {/* Trust Note */}
      <div className="flex items-center justify-center gap-2 py-2 text-ink-soft text-[11.5px] border-t border-line/50 mt-1">
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          className="text-trust flex-shrink-0"
        >
          <path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5z" />
        </svg>
        <span>Basis data diverifikasi apoteker terdaftar</span>
      </div>
    </div>
  );
}
