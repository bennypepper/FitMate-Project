"use client";

import { useEffect, useState, useRef } from "react";
import QRCode from "qrcode";
import { getApiBaseUrl } from "@/lib/apiConfig";

interface QRCodeBridgeProps {
  onComplete: (results: any) => void;
}

export default function QRCodeBridge({ onComplete }: QRCodeBridgeProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [mobileLink, setMobileLink] = useState<string>("");
  const [status, setStatus] = useState<"loading" | "waiting" | "processing" | "completed" | "error">("loading");
  const [copied, setCopied] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const apiUrl = getApiBaseUrl();

  // 1. Create session & render QR instantly on mount (<10ms)
  useEffect(() => {
    let isMounted = true;

    async function initSession() {
      try {
        // Generate unique session ID client-side immediately
        const sid = `fm_${Math.random().toString(36).substring(2, 8)}${Date.now().toString(36).slice(-4)}`;
        const origin = typeof window !== "undefined" ? window.location.origin : "https://fitmate-project.vercel.app";
        const targetUrl = `${origin}/?session=${sid}`;

        if (!isMounted) return;
        setSessionId(sid);
        setMobileLink(targetUrl);

        // Generate dynamic QR Code Data URL instantly in browser memory
        const qrData = await QRCode.toDataURL(targetUrl, {
          margin: 1.5,
          width: 200,
          color: {
            dark: "#211C17",
            light: "#FFFFFF",
          },
        });

        if (!isMounted) return;
        setQrUrl(qrData);
        setStatus("waiting");

        // Asynchronously register session with backend (non-blocking)
        fetch(`${apiUrl}/api/v1/bridge/session?custom_id=${sid}`, { method: "POST" }).catch((e) => {
          console.warn("[Bridge Session Register Warning]", e);
        });
      } catch (err) {
        console.error("[Bridge Init Error]", err);
        if (isMounted) setStatus("error");
      }
    }

    initSession();

    return () => {
      isMounted = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [apiUrl]);

  // 2. Poll session status every 2 seconds when waiting or processing
  useEffect(() => {
    if (!sessionId || status === "completed" || status === "error") {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    intervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${apiUrl}/api/v1/bridge/${sessionId}/status`);
        if (res.status === 404) {
          setStatus("error");
          if (intervalRef.current) clearInterval(intervalRef.current);
          return;
        }
        if (!res.ok) return;

        const data = await res.json();
        if (data.status === "processing") {
          setStatus("processing");
        } else if (data.status === "completed" && data.results) {
          setStatus("completed");
          if (intervalRef.current) clearInterval(intervalRef.current);
          onComplete(data.results);
        } else if (data.status === "error") {
          setStatus("error");
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
      } catch (err) {
        console.warn("[Bridge Polling Warning]", err);
      }
    }, 2000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [sessionId, status, apiUrl, onComplete]);

  const handleCopyLink = () => {
    if (!mobileLink) return;
    navigator.clipboard.writeText(mobileLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-card border border-line rounded-[16px] p-4.5 shadow-xs flex flex-col sm:flex-row items-center gap-4">
      {/* QR Code Container */}
      <div className="w-[110px] h-[110px] sm:w-[120px] sm:h-[120px] bg-white p-1.5 rounded-[12px] border border-line shadow-xs flex items-center justify-center flex-shrink-0">
        {status === "loading" && (
          <div className="text-[11px] text-ink-faint flex flex-col items-center gap-1">
            <span className="animate-spin text-sm">⏳</span>
            <span>Membuat QR...</span>
          </div>
        )}
        {status === "error" && (
          <div className="text-[10px] text-danger text-center px-1">
            Gagal memuat QR
          </div>
        )}
        {qrUrl && status !== "loading" && status !== "error" && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={qrUrl}
            alt="Pindai dengan kamera ponsel"
            className="w-full h-full object-contain rounded-[8px]"
          />
        )}
      </div>

      {/* Description & Status */}
      <div className="flex-1 flex flex-col items-start text-left">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-semibold text-[13px] text-ink">
            Pindai kode ini dengan kamera HP
          </span>
        </div>

        {/* Live Status Pill */}
        <div className="inline-flex items-center gap-1.5 mb-2 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-paper-deep text-ink-soft">
          {status === "waiting" && (
            <>
              <span className="w-2 h-2 rounded-full bg-trust animate-pulse" />
              <span>Menunggu pindaian ponsel...</span>
            </>
          )}
          {status === "processing" && (
            <>
              <span className="w-2 h-2 rounded-full bg-amber animate-spin" />
              <span className="text-amber font-semibold">Sedang menganalisis label dari HP...</span>
            </>
          )}
          {status === "completed" && (
            <>
              <span className="w-2 h-2 rounded-full bg-trust" />
              <span className="text-trust-deep font-semibold">Selesai! Menampilkan di layar...</span>
            </>
          )}
          {status === "loading" && <span>Menghubungkan ke server...</span>}
          {status === "error" && (
            <span className="text-danger">Sesi kadaluarsa. Refresh untuk mengulang.</span>
          )}
        </div>

        <p className="text-[11.5px] leading-relaxed text-ink-soft mb-2.5">
          Buka kamera smartphone dan scan kode di samping untuk memotret label. Hasil analisis otomatis muncul di monitor ini.
        </p>

        {mobileLink && (
          <div className="flex items-center gap-3 flex-wrap">
            <button
              type="button"
              onClick={handleCopyLink}
              className="text-[11px] font-semibold text-trust hover:text-trust-deep underline decoration-trust/40 underline-offset-2 flex items-center gap-1 cursor-pointer"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              <span>{copied ? "✓ Tautan Tersalin!" : "Salin Tautan HP"}</span>
            </button>
            <a
              href={mobileLink}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] font-semibold text-ink-soft hover:text-ink underline decoration-line underline-offset-2 flex items-center gap-1"
            >
              <span>↗ Uji Buka di Tab Baru</span>
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
