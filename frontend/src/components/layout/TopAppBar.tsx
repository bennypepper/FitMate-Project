"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function TopAppBar() {
  const pathname = usePathname();

  // Do not show consumer nav inside admin dashboard to prevent clutter
  if (pathname.startsWith("/admin")) {
    return null;
  }

  return (
    <header className="w-full bg-paper border-b border-line sticky top-0 z-40">
      <div className="max-w-[1200px] mx-auto px-6 md:px-9 py-4 flex items-center justify-between">
        <Link
          href="/"
          className="font-serif text-xl font-bold italic text-heritage tracking-tight hover:opacity-90 transition-opacity"
        >
          FitMate TCM
        </Link>

        <nav className="hidden md:flex items-center gap-8 text-[13.5px] font-medium text-ink-soft">
          <Link
            href="/"
            className={`transition-colors hover:text-ink ${
              pathname === "/" ? "text-ink font-semibold" : ""
            }`}
          >
            Pindai
          </Link>
          <Link
            href="/admin/ingredients"
            className="transition-colors hover:text-ink"
          >
            Basis Data Bahan
          </Link>
          <a
            href="#cara-kerja"
            className="transition-colors hover:text-ink"
          >
            Cara Kerja
          </a>
          <a
            href="#tentang"
            className="transition-colors hover:text-ink"
          >
            Tentang
          </a>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/admin/login"
            className="px-4 py-2 text-[13px] font-semibold text-ink border border-line rounded-[10px] hover:bg-paper-deep transition-colors"
          >
            Masuk
          </Link>
          <Link
            href="/admin"
            className="px-4 py-2 text-[13px] font-semibold text-white bg-trust hover:bg-trust-deep rounded-[10px] transition-colors shadow-sm flex items-center gap-1.5"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <path d="M9 3v18" />
              <path d="M14 9h5" />
              <path d="M14 15h5" />
            </svg>
            Admin Console
          </Link>
        </div>
      </div>
    </header>
  );
}
