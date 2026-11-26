"use client";

import { useState, useEffect, useMemo } from "react";
import { getApiBaseUrl } from "@/lib/apiConfig";

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

const PAGE_SIZE = 50;

let cachedCatalog: IngredientItem[] | null = null;
let catalogPromise: Promise<IngredientItem[]> | null = null;

async function loadTcmCatalog(): Promise<IngredientItem[]> {
  if (cachedCatalog) return cachedCatalog;
  if (!catalogPromise) {
    catalogPromise = import("@/data/tcmIngredients.json")
      .then((mod) => {
        const items = (
          (mod as { default?: IngredientItem[] }).default ?? mod
        ) as IngredientItem[];
        cachedCatalog = items;
        return items;
      })
      .catch((err) => {
        catalogPromise = null;
        throw err;
      });
  }
  return catalogPromise;
}

interface IngredientSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function IngredientSearchModal({
  isOpen,
  onClose,
}: IngredientSearchModalProps) {
  if (!isOpen) return null;
  return <IngredientSearchModalContent onClose={onClose} />;
}

function IngredientSearchModalContent({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [filterType, setFilterType] = useState<"all" | "toxic" | "safe">("all");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [catalogItems, setCatalogItems] = useState<IngredientItem[]>(
    () => cachedCatalog ?? []
  );
  const [catalogLoading, setCatalogLoading] = useState(() => !cachedCatalog);
  const [catalogError, setCatalogError] = useState(false);
  const [searchResults, setSearchResults] = useState<IngredientItem[] | null>(null);
  const [loading, setLoading] = useState(false);

  const handleQueryChange = (nextValue: string) => {
    setQuery(nextValue);
    setVisibleCount(PAGE_SIZE);
    if (!nextValue.trim()) {
      setSearchResults(null);
      setLoading(false);
    }
  };

  // Lazy-load the 1,500-item catalog only on first modal open
  useEffect(() => {
    if (cachedCatalog) return;

    let cancelled = false;
    loadTcmCatalog()
      .then((items) => {
        if (!cancelled) {
          setCatalogItems(items);
          setCatalogLoading(false);
          setCatalogError(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load TCM catalog:", err);
        if (!cancelled) {
          setCatalogError(true);
          setCatalogLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // Handle Search with AbortController + 5s timeout
  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) return;

    let cancelled = false;
    let activeController: AbortController | null = null;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const performClientFallback = async (searchTerm: string) => {
      try {
        const items = cachedCatalog ?? (await loadTcmCatalog());
        if (cancelled) return;
        const q = searchTerm.toLowerCase();
        const matched = items.filter((item) => {
          return (
            item.indonesian_name?.toLowerCase().includes(q) ||
            item.mandarin_name?.toLowerCase().includes(q) ||
            item.pinyin_name?.toLowerCase().includes(q) ||
            (item.english_name && item.english_name.toLowerCase().includes(q)) ||
            (item.latin_name && item.latin_name.toLowerCase().includes(q)) ||
            (item.target_organ && item.target_organ.toLowerCase().includes(q)) ||
            (item.description && item.description.toLowerCase().includes(q)) ||
            (item.source_reference && item.source_reference.toLowerCase().includes(q))
          );
        });
        setSearchResults(matched);
      } catch (err) {
        console.warn("Local catalog search fallback failed:", err);
        if (!cancelled) {
          setSearchResults([]);
        }
      }
    };

    const fetchIngredients = async () => {
      setLoading(true);
      const controller = new AbortController();
      activeController = controller;
      let timedOut = false;
      timeoutId = setTimeout(() => {
        timedOut = true;
        controller.abort();
      }, 5000);

      try {
        const apiUrl = getApiBaseUrl();
        const res = await fetch(
          `${apiUrl}/api/v1/analyze/search?q=${encodeURIComponent(trimmed)}&limit=50`,
          { signal: controller.signal }
        );
        if (timeoutId) clearTimeout(timeoutId);
        if (cancelled) return;

        if (res.ok) {
          const data = await res.json();
          if (!cancelled) {
            setSearchResults(data.items || []);
          }
        } else {
          // Client-side fallback if API is unreachable or returned non-OK
          await performClientFallback(trimmed);
        }
      } catch (err) {
        if (timeoutId) clearTimeout(timeoutId);
        if (cancelled && !timedOut) return;
        console.warn("API search failed, falling back to local dataset:", err);
        await performClientFallback(trimmed);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    const debounceTimer = setTimeout(fetchIngredients, 250);
    return () => {
      cancelled = true;
      clearTimeout(debounceTimer);
      if (timeoutId) clearTimeout(timeoutId);
      if (activeController) activeController.abort();
    };
  }, [query]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const activeBaseList = useMemo(
    () => (searchResults !== null ? searchResults : catalogItems),
    [searchResults, catalogItems]
  );

  // Compute displayed list with filterType applied
  const displayedItems = useMemo(() => {
    if (filterType === "toxic") {
      return activeBaseList.filter((item) => item.is_toxic);
    }
    if (filterType === "safe") {
      return activeBaseList.filter((item) => !item.is_toxic);
    }
    return activeBaseList;
  }, [activeBaseList, filterType]);

  const visibleItems = useMemo(
    () => displayedItems.slice(0, visibleCount),
    [displayedItems, visibleCount]
  );

  const totalAll = activeBaseList.length;
  const totalToxic = useMemo(
    () => activeBaseList.filter((item) => item.is_toxic).length,
    [activeBaseList]
  );
  const totalSafe = useMemo(
    () => activeBaseList.filter((item) => !item.is_toxic).length,
    [activeBaseList]
  );

  const formattedCatalogCount =
    catalogItems.length > 0 ? catalogItems.length.toLocaleString("id-ID") : "1.500";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Kamus Bahan TCM dan Toksisitas"
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
                Katalog kompilasi {formattedCatalogCount} bahan TCM &amp; herbal rujukan resmi BPOM, Kemenkes FHI, SymMap, HKCMMS, ChP 2020 &amp; EFSA
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
              onChange={(e) => handleQueryChange(e.target.value)}
              placeholder="Cari nama herbal (contoh: Fu Zi, Ginseng, Aconite, Gan Cao)..."
              autoFocus
              className="w-full bg-card border border-line rounded-[12px] pl-11 pr-10 py-3 text-[14px] text-ink focus:outline-none focus:border-trust focus:ring-2 focus:ring-trust-tint transition-all placeholder:text-ink-faint"
            />
            <div className="absolute left-3.5 top-3.5 text-ink-soft">
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
                onClick={() => handleQueryChange("")}
                className="absolute right-3.5 top-3.5 text-ink-soft hover:text-ink transition-colors text-xs cursor-pointer p-1"
                aria-label="Hapus pencarian"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            )}
          </div>

          {/* Quick Filter Chips */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <button
              onClick={() => {
                setFilterType("all");
                setVisibleCount(PAGE_SIZE);
              }}
              className={`px-3 py-1.5 rounded-full font-medium transition-all cursor-pointer whitespace-nowrap ${
                filterType === "all"
                  ? "bg-trust text-white shadow-xs"
                  : "bg-card border border-line text-ink-soft hover:text-ink"
              }`}
            >
              Semua Bahan ({totalAll.toLocaleString("id-ID")})
            </button>
            <button
              onClick={() => {
                setFilterType("toxic");
                setVisibleCount(PAGE_SIZE);
              }}
              className={`px-3 py-1.5 rounded-full font-medium transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
                filterType === "toxic"
                  ? "bg-danger text-white shadow-xs"
                  : "bg-danger-tint/30 text-danger-deep border border-danger/20 hover:bg-danger-tint/60"
              }`}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <span>Toksik / Dibatasi ({totalToxic.toLocaleString("id-ID")})</span>
            </button>
            <button
              onClick={() => {
                setFilterType("safe");
                setVisibleCount(PAGE_SIZE);
              }}
              className={`px-3 py-1.5 rounded-full font-medium transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
                filterType === "safe"
                  ? "bg-trust-deep text-white shadow-xs"
                  : "bg-trust-tint/40 text-trust-deep border border-trust/20 hover:bg-trust-tint/70"
              }`}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>Aman ({totalSafe.toLocaleString("id-ID")})</span>
            </button>
          </div>
        </div>

        {/* Results / Default List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-3">
          {(loading || (catalogLoading && searchResults === null)) && (
            <div className="py-12 text-center text-ink-soft text-sm flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4 text-trust" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>
                {loading ? "Mencari bahan herbal..." : "Memuat katalog 1.500 bahan herbal..."}
              </span>
            </div>
          )}

          {!loading && !catalogLoading && catalogError && searchResults === null && catalogItems.length === 0 && (
            <div className="py-12 text-center">
              <p className="text-[14px] font-semibold text-ink mb-1">
                Gagal memuat katalog lokal
              </p>
              <p className="text-[12px] text-ink-soft">
                Silakan tutup dan buka kembali kamus, atau gunakan kotak pencarian untuk mencari via server.
              </p>
            </div>
          )}

          {!loading && !(catalogLoading && searchResults === null) && !(catalogError && searchResults === null && catalogItems.length === 0) && displayedItems.length === 0 && (
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
                  setVisibleCount(PAGE_SIZE);
                }}
                className="px-4 py-2 text-xs font-semibold bg-trust-tint text-trust-deep rounded-full hover:bg-trust/20 transition-colors cursor-pointer"
              >
                Tampilkan Semua Bahan
              </button>
            </div>
          )}

          {!loading && !(catalogLoading && searchResults === null) && displayedItems.length > 0 && (
            <>
              {/* Section Subtitle */}
              <div className="flex items-center justify-between text-[11.5px] text-ink-soft font-semibold px-1 pb-1">
                <span>
                  {query
                    ? `Hasil pencarian untuk "${query}"`
                    : filterType === "toxic"
                    ? "Daftar bahan berisiko & diawasi ketat"
                    : filterType === "safe"
                    ? "Daftar herbal umum & suplemen aman"
                    : "Daftar herbal TCM & suplemen terkurasi"}
                </span>
                <span>{displayedItems.length.toLocaleString("id-ID")} bahan</span>
              </div>

              {visibleItems.map((item, idx) => (
                <div
                  key={`${item.mandarin_name}-${item.indonesian_name}-${idx}`}
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

                  <div className="flex items-center justify-between text-[11px] text-ink-soft mt-2.5 pt-2 border-t border-line/60">
                    <div className="flex items-center gap-1.5">
                      <span>Organ sasaran:</span>
                      <span className="font-medium text-ink">
                        {item.target_organ || "Umum"}
                      </span>
                    </div>
                    {item.source_reference && (
                      <span className="text-[10.5px] text-ink-soft font-medium bg-paper px-2 py-0.5 rounded-md border border-line">
                        Ref: {item.source_reference}
                      </span>
                    )}
                  </div>
                </div>
              ))}

              {visibleItems.length < displayedItems.length && (
                <div className="pt-2 pb-1 flex justify-center">
                  <button
                    type="button"
                    onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
                    className="px-4 py-2.5 text-xs font-semibold bg-card border border-line text-ink hover:border-trust/50 hover:bg-trust-tint/30 rounded-[12px] transition-colors cursor-pointer"
                  >
                    Muat lebih banyak (menampilkan {visibleItems.length.toLocaleString("id-ID")} dari{" "}
                    {displayedItems.length.toLocaleString("id-ID")} bahan)
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 sm:p-4 border-t border-line bg-paper-deep text-center text-[11.5px] text-ink-soft">
          Basis data dikompilasi dari rujukan resmi BPOM, Kemenkes FHI, SymMap, HKCMMS, ChP 2020 &amp; EFSA sebagai referensi edukasi awal, bukan pengganti konsultasi dokter.
        </div>
      </div>
    </div>
  );
}
