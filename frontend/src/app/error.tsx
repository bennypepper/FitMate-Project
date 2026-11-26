"use client";

import Link from "next/link";
import { useEffect } from "react";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    console.error("[App Error Boundary]", error);
  }, [error]);

  return (
    <div className="flex-1 flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md bg-card border border-line rounded-[20px] p-8 text-center shadow-sm">
        <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-danger-tint text-danger flex items-center justify-center">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <h1 className="font-serif text-2xl font-bold text-ink mb-2">
          Terjadi Kendala Tak Terduga
        </h1>
        <p className="text-[13.5px] text-ink-soft leading-relaxed mb-6">
          Maaf, halaman tidak dapat dimuat dengan benar saat ini. Silakan coba
          muat ulang atau kembali ke beranda.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            onClick={reset}
            className="px-5 py-2.5 rounded-[10px] bg-trust hover:bg-trust-deep text-white text-[13px] font-semibold transition cursor-pointer"
          >
            Coba Lagi
          </button>
          <Link
            href="/"
            className="px-5 py-2.5 rounded-[10px] bg-paper-deep hover:bg-paper text-ink text-[13px] font-semibold border border-line transition"
          >
            Kembali ke Beranda
          </Link>
        </div>
      </div>
    </div>
  );
}
