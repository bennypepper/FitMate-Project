"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import IngredientSearchModal from "@/components/search/IngredientSearchModal";

export default function TopAppBar() {
  const pathname = usePathname();
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // Do not show consumer nav inside admin dashboard to prevent clutter
  if (pathname.startsWith("/admin")) {
    return null;
  }

  return (
    <>
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
            <button
              onClick={() => setIsSearchOpen(true)}
              className="px-3.5 py-2 text-[13px] font-semibold text-trust-deep bg-trust-tint hover:bg-trust/20 rounded-[10px] transition-colors flex items-center gap-2 cursor-pointer shadow-xs"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <span className="hidden sm:inline">Kamus Bahan TCM</span>
              <span className="sm:hidden">Kamus TCM</span>
            </button>
          </div>
        </div>
      </header>

      <IngredientSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
      />
    </>
  );
}

