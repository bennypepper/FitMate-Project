"use client";

import { useEffect, useState, useRef } from "react";
import QRCode from "qrcode";
import { getApiBaseUrl } from "@/lib/apiConfig";
import { AnalyzeApiResponse } from "@/types/tcm";

interface QRCodeBridgeProps {
  onComplete: (results: AnalyzeApiResponse) => void;
}

const SESSION_DEADLINE_MS = 300_000;
const BASE_POLL_INTERVAL_MS = 2_000;
const MAX_BACKOFF_MS = 16_000;

export default function QRCodeBridge({ onComplete }: QRCodeBridgeProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [mobileLink, setMobileLink] = useState<string>("");
  const [status, setStatus] = useState<
    "loading" | "waiting" | "processing" | "completed" | "error"
  >("loading");
  const [copied, setCopied] = useState(false);

  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  // 1. Register bridge session with backend to receive session_id & upload_token, then render QR
  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();

    async function initSession() {
      try {
        const apiUrl = getApiBaseUrl();
        const timeoutId = setTimeout(() => controller.abort(), 10_000);
        const res = await fetch(`${apiUrl}/api/v1/bridge/session`, {
          method: "POST",
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (!res.ok) {
          throw new Error(`Gagal membuat sesi jembatan (${res.status})`);
        }

        const data: { session_id?: string; upload_token?: string } = await res.json();
        const sid = data.session_id;
        if (!sid) {
          throw new Error("Respons sesi jembatan tidak valid");
        }

        const uploadToken = data.upload_token;
        const origin =
          typeof window !== "undefined"
            ? window.location.origin
            : "https://fitmate-project.vercel.app";
        const tokenQuery = uploadToken
          ? `&token=${encodeURIComponent(uploadToken)}`
          : "";
        const targetUrl = `${origin}/?session=${encodeURIComponent(sid)}${tokenQuery}`;

        const qrData = await QRCode.toDataURL(targetUrl, {
          margin: 1.5,
          width: 200,
          color: {
            dark: "#211C17",
            light: "#FFFFFF",
          },
        });

        if (!isMounted) return;
        setSessionId(sid);
        setMobileLink(targetUrl);
        setQrUrl(qrData);
        setStatus("waiting");
      } catch (err) {
        if (controller.signal.aborted) return;
        console.error("[Bridge Init Error]", err);
        if (isMounted) setStatus("error");
      }
    }

    initSession();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, []);

  // 2. Poll session status via recursive setTimeout with AbortController, 5-min deadline, and backoff
  useEffect(() => {
    if (!sessionId || status === "completed" || status === "error") {
      return;
    }

    let isMounted = true;
    let timerId: ReturnType<typeof setTimeout> | null = null;
    let activeController: AbortController | null = null;
    let consecutiveFailures = 0;
    const deadline = Date.now() + SESSION_DEADLINE_MS;
    const apiUrl = getApiBaseUrl();

    const scheduleNext = (delayMs: number) => {
      if (!isMounted) return;
      timerId = setTimeout(pollOnce, delayMs);
    };

    const pollOnce = async () => {
      if (!isMounted) return;

      if (Date.now() >= deadline) {
        setStatus("error");
        return;
      }

      activeController = new AbortController();
      const timeoutId = setTimeout(() => activeController?.abort(), 5_000);

      try {
        const res = await fetch(
          `${apiUrl}/api/v1/bridge/${encodeURIComponent(sessionId)}/status`,
          { signal: activeController.signal }
        );
        clearTimeout(timeoutId);

        if (!isMounted) return;

        if (res.status === 404) {
          setStatus("error");
          return;
        }

        if (!res.ok) {
          consecutiveFailures += 1;
          const backoff = Math.min(
            BASE_POLL_INTERVAL_MS * Math.pow(2, consecutiveFailures),
            MAX_BACKOFF_MS
          );
          scheduleNext(backoff);
          return;
        }

        consecutiveFailures = 0;
        const data = await res.json();
        if (!isMounted) return;

        if (data.status === "processing") {
          setStatus("processing");
          scheduleNext(BASE_POLL_INTERVAL_MS);
        } else if (data.status === "completed" && data.results) {
          setStatus("completed");
          onCompleteRef.current(data.results);
        } else if (data.status === "error") {
          setStatus("error");
        } else {
          scheduleNext(BASE_POLL_INTERVAL_MS);
        }
      } catch (err) {
        clearTimeout(timeoutId);
        if (!isMounted) return;
        console.warn("[Bridge Polling Warning]", err);
        consecutiveFailures += 1;
        const backoff = Math.min(
          BASE_POLL_INTERVAL_MS * Math.pow(2, consecutiveFailures),
          MAX_BACKOFF_MS
        );
        scheduleNext(backoff);
      }
    };

    scheduleNext(BASE_POLL_INTERVAL_MS);

    return () => {
      isMounted = false;
      if (timerId) clearTimeout(timerId);
      if (activeController) activeController.abort();
    };
  }, [sessionId, status]);

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
          <div className="text-[11px] text-ink-soft font-medium flex flex-col items-center gap-1.5">
            <svg
              className="animate-spin h-5 w-5 text-trust"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
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
              <span className="text-amber font-semibold">
                Sedang menganalisis label dari HP...
              </span>
            </>
          )}
          {status === "completed" && (
            <>
              <span className="w-2 h-2 rounded-full bg-trust" />
              <span className="text-trust-deep font-semibold">
                Selesai! Menampilkan di layar...
              </span>
            </>
          )}
          {status === "loading" && <span>Menghubungkan ke server...</span>}
          {status === "error" && (
            <span className="text-danger">
              Sesi kadaluarsa. Refresh untuk mengulang.
            </span>
          )}
        </div>

        <p className="text-[11.5px] leading-relaxed text-ink-soft mb-2.5">
          Buka kamera smartphone dan scan kode di samping untuk memotret label.
          Hasil analisis otomatis muncul di monitor ini.
        </p>

        {mobileLink && status !== "error" && (
          <div className="flex items-center gap-3 flex-wrap">
            <button
              type="button"
              onClick={handleCopyLink}
              className="text-[11px] font-semibold text-trust hover:text-trust-deep underline decoration-trust/40 underline-offset-2 flex items-center gap-1 cursor-pointer"
            >
              {copied ? (
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-trust-deep"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              ) : (
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="9" y="9" width="13" height="13" rx="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
              )}
              <span>{copied ? "Tautan Tersalin!" : "Salin Tautan HP"}</span>
            </button>
            <a
              href={mobileLink}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] font-semibold text-ink-soft hover:text-ink underline decoration-line underline-offset-2 flex items-center gap-1"
            >
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
              <span>Uji Buka di Tab Baru</span>
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
