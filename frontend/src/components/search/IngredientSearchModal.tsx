"use client";

import { useState, useEffect, useMemo } from "react";
import { getApiBaseUrl } from "@/lib/apiConfig";
import rawTcmData from "@/data/tcmIngredients.json";

export interface IngredientItem {
  mandarin_name: string;
  pinyin_name?: string;
  indonesian_name: string;
  english_name?: string;
  latin_name?: string;
  is_toxic: boolean;
  toxicity_level?: string;
  target_organ?: string;
  description?: string;
  source_reference?: string;
}

const DEFAULT_INGREDIENTS: IngredientItem[] = rawTcmData as IngredientItem[];

interface IngredientSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function IngredientSearchModal({
  isOpen,
  onClose,
}: IngredientSearchModalProps) {
  const [query, setQuery] = useState("");
  const [filterType, setFilterType] = useState<"all" | "toxic" | "safe">("all");
  const [searchResults, setSearchResults] = useState<IngredientItem[] | null>(null);
  const [loading, setLoading] = useState(false);

  // Reset states on modal open/close
  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setFilterType("all");
      setSearchResults(null);
    }
  }, [isOpen]);

  // Handle Search
  useEffect(() => {
    if (!isOpen) return;

    const trimmed = query.trim();
    if (!trimmed) {
      setSearchResults(null);
      setLoading(false);
      return;
    }

    const fetchIngredients = async () => {
      setLoading(true);
      try {
        const apiUrl = getApiBaseUrl();
        const res = await fetch(
          `${apiUrl}/api/v1/analyze/search?q=${encodeURIComponent(trimmed)}&limit=30`
        );
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data.items || []);
        } else {
          // Client-side fallback if API is unreachable or returned 404
          performClientFallback(trimmed);
        }
      } catch (err) {
        console.warn("API search failed, falling back to local dataset:", err);
        performClientFallback(trimmed);
      } finally {
        setLoading(false);
      }
    };

    const performClientFallback = (searchTerm: string) => {
      const q = searchTerm.toLowerCase();
      const matched = DEFAULT_INGREDIENTS.filter((item) => {
        return (
          item.indonesian_name?.toLowerCase().includes(q) ||
          item.mandarin_name?.toLowerCase().includes(q) ||
          item.pinyin_name?.toLowerCase().includes(q) ||
          (item.english_name && item.english_name.toLowerCase().includes(q)) ||
          (item.target_organ && item.target_organ.toLowerCase().includes(q)) ||
          (item.description && item.description.toLowerCase().includes(q))
        );
      });
      setSearchResults(matched);
    };

    const debounceTimer = setTimeout(fetchIngredients, 250);
    return () => clearTimeout(debounceTimer);
  }, [query, isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Compute displayed list with filterType applied
  const displayedItems = useMemo(() => {
    const baseList = searchResults !== null ? searchResults : DEFAULT_INGREDIENTS;
    if (filterType === "toxic") {
      return baseList.filter((item) => item.is_toxic);
    }
    if (filterType === "safe") {
      return baseList.filter((item) => !item.is_toxic);
    }
    return baseList;
  }, [searchResults, filterType]);

  const totalToxic = useMemo(
    () => DEFAULT_INGREDIENTS.filter((item) => item.is_toxic).length,
    []
  );
  const totalSafe = useMemo(
    () => DEFAULT_INGREDIENTS.filter((item) => !item.is_toxic).length,
    []
  );

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-paper w-full max-w-2xl rounded-[20px] border border-line shadow-2xl overflow-hidden flex flex-col max-h-[88vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 sm:p-6 border-b border-line flex items-center justify-between bg-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-trust-tint text-trust-deep flex items-center justify-center flex-shrink-0">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
            <div>
              <h3 className="font-serif text-lg font-bold text-ink">
                Kamus Bahan TCM &amp; Toksisitas
              </h3>
              <p className="text-[12px] text-ink-soft">
                Basis data 101 herbal terverifikasi BPOM &amp; monograf TCM
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-paper-deep hover:bg-line text-ink flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Tutup modal"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Search Input & Quick Filter Chips */}
        <div className="p-4 border-b border-line bg-paper space-y-3">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Cari nama herbal (contoh: Fu Zi, Ginseng, Aconite, Gan Cao)..."
              autoFocus
              className="w-full bg-card border border-line rounded-[12px] pl-11 pr-10 py-3 text-[14px] text-ink focus:outline-none focus:border-trust focus:ring-2 focus:ring-trust-tint transition-all placeholder:text-ink-faint"
            />
            <div className="absolute left-3.5 top-3.5 text-ink-faint">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
            {query && (
              <button
                onClick={() => setQuery("")}
                className="absolute right-3.5 top-3.5 text-ink-faint hover:text-ink transition-colors text-xs cursor-pointer p-1"
                aria-label="Hapus pencarian"
              >
                ✕
              </button>
            )}
          </div>

          {/* Quick Filter Chips */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <button
              onClick={() => setFilterType("all")}
              className={`px-3 py-1.5 rounded-full font-medium transition-all cursor-pointer whitespace-nowrap ${
                filterType === "all"
                  ? "bg-trust text-white shadow-xs"
                  : "bg-card border border-line text-ink-soft hover:text-ink"
              }`}
            >
              Semua Bahan ({searchResults !== null ? searchResults.length : DEFAULT_INGREDIENTS.length})
            </button>
            <button
              onClick={() => setFilterType("toxic")}
              className={`px-3 py-1.5 rounded-full font-medium transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
                filterType === "toxic"
                  ? "bg-danger text-white shadow-xs"
                  : "bg-danger-tint/30 text-danger-deep border border-danger/20 hover:bg-danger-tint/60"
              }`}
            >
              <span>⚠️ Berisiko / Toksik ({totalToxic})</span>
            </button>
            <button
              onClick={() => setFilterType("safe")}
              className={`px-3 py-1.5 rounded-full font-medium transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
                filterType === "safe"
                  ? "bg-trust-deep text-white shadow-xs"
                  : "bg-trust-tint/40 text-trust-deep border border-trust/20 hover:bg-trust-tint/70"
              }`}
            >
              <span>✅ Aman / Suplemen ({totalSafe})</span>
            </button>
          </div>
        </div>

        {/* Results / Default List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-3">
          {loading && (
            <div className="py-12 text-center text-ink-soft text-sm">
              <span className="inline-block animate-spin mr-2">⏳</span> Mencari bahan herbal...
            </div>
          )}

          {!loading && displayedItems.length === 0 && (
            <div className="py-12 text-center">
              <p className="text-[14px] font-semibold text-ink mb-1">
                {query
                  ? `Tidak ada bahan yang cocok dengan "${query}"`
                  : "Tidak ada bahan pada kategori ini"}
              </p>
              <p className="text-[12px] text-ink-soft mb-4">
                Coba kata kunci lain seperti nama latin, Indonesia, atau organ sasaran.
              </p>
              <button
                onClick={() => {
                  setQuery("");
                  setFilterType("all");
                }}
                className="px-4 py-2 text-xs font-semibold bg-trust-tint text-trust-deep rounded-full hover:bg-trust/20 transition-colors cursor-pointer"
              >
                Tampilkan Semua Bahan
              </button>
            </div>
          )}

          {!loading && displayedItems.length > 0 && (
            <>
              {/* Section Subtitle */}
              <div className="flex items-center justify-between text-[11.5px] text-ink-faint px-1 pb-1">
                <span>
                  {query
                    ? `Hasil pencarian untuk "${query}"`
                    : filterType === "toxic"
                    ? "Daftar bahan berisiko & diawasi ketat"
                    : filterType === "safe"
                    ? "Daftar herbal umum & suplemen aman"
                    : "Daftar herbal TCM terpopuler"}
                </span>
                <span>{displayedItems.length} bahan</span>
              </div>

              {displayedItems.map((item, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-[14px] border transition-all ${
                    item.is_toxic
                      ? "bg-danger-tint/30 border-danger/30 hover:border-danger/60"
                      : "bg-card border-line hover:border-trust/40"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-1.5">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-serif font-bold text-[16px] text-ink">
                          {item.mandarin_name}
                        </span>
                        {item.pinyin_name && (
                          <span className="text-[12.5px] font-medium text-ink-soft">
                            · {item.pinyin_name}
                          </span>
                        )}
                      </div>
                      <div className="text-[13.5px] font-semibold text-ink mt-0.5">
                        {item.indonesian_name}
                        {item.english_name && item.english_name !== "-" && (
                          <span className="text-[12px] font-normal text-ink-soft ml-1.5">
                            ({item.english_name})
                          </span>
                        )}
                      </div>
                    </div>

                    <span
                      className={`px-2.5 py-1 rounded-full text-[10.5px] font-bold tracking-wide flex-shrink-0 ${
                        item.is_toxic
                          ? "bg-danger text-white shadow-xs"
                          : "bg-trust-tint text-trust-deep"
                      }`}
                    >
                      {item.is_toxic ? "BERISIKO / TOKSIK" : "AMAN"}
                    </span>
                  </div>

                  {item.description && (
                    <p className="text-[12px] leading-relaxed text-ink-soft mt-1">
                      {item.description}
                    </p>
                  )}

                  <div className="flex items-center justify-between text-[11px] text-ink-faint mt-2.5 pt-2 border-t border-line/60">
                    <div className="flex items-center gap-1.5">
                      <span>Organ sasaran:</span>
                      <span className="font-medium text-ink-soft">
                        {item.target_organ || "Umum"}
                      </span>
                    </div>
                    {item.source_reference && (
                      <span className="text-[10px] text-ink-faint bg-paper px-2 py-0.5 rounded-md border border-line">
                        Ref: {item.source_reference}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 sm:p-4 border-t border-line bg-paper-deep text-center text-[11.5px] text-ink-soft">
          Semua data telah diverifikasi sesuai monograf TCM &amp; BPOM untuk pencegahan risiko kesehatan.
        </div>
      </div>
    </div>
  );
}
