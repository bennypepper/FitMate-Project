"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getIngredients } from "@/lib/adminApi";
import { useRouter } from "next/navigation";

interface Ingredient {
  _id: string;
  mandarin_name: string;
  indonesian_name: string;
  latin_name?: string;
  english_name?: string;
  is_toxic: boolean;
  toxicity_level?: string;
}

type BadgeConfig = { label: string; className: string };

const TOXICITY_BADGES: Record<string, BadgeConfig> = {
  high: {
    label: "Risiko Tinggi",
    className: "bg-danger text-white font-bold",
  },
  moderate: {
    label: "Sedang",
    className: "bg-amber-tint text-amber font-semibold border border-amber/30",
  },
  low: {
    label: "Rendah",
    className: "bg-paper-deep text-ink-soft border border-line",
  },
  unknown: {
    label: "Tidak Diketahui",
    className: "bg-paper-deep text-ink-soft border border-line",
  },
};

const SAFE_BADGE: BadgeConfig = {
  label: "Aman",
  className: "bg-trust-tint text-trust-deep font-bold border border-trust/20",
};

export default function IngredientsPage() {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    let isCurrent = true;
    getIngredients(page, 20, debouncedSearch)
      .then((data: { ingredients: Ingredient[]; total: number; pages: number }) => {
        if (isCurrent) {
          setIngredients(data.ingredients);
          setTotal(data.total);
          setPages(data.pages);
        }
      })
      .catch((err: Error) => {
        if (isCurrent && err.message === "Unauthorized") {
          router.replace("/admin/login");
        }
      })
      .finally(() => {
        if (isCurrent) setLoading(false);
      });

    return () => {
      isCurrent = false;
    };
  }, [page, debouncedSearch, router]);

  const filtered = ingredients;

  const getBadge = (ing: Ingredient): BadgeConfig => {
    if (!ing.is_toxic) return SAFE_BADGE;
    return TOXICITY_BADGES[ing.toxicity_level ?? "unknown"] ?? TOXICITY_BADGES.unknown;
  };

  const safePages = Math.max(1, pages);
  const windowSize = Math.min(5, safePages);
  const halfWindow = Math.floor(windowSize / 2);
  let startPage = Math.max(1, page - halfWindow);
  let endPage = startPage + windowSize - 1;
  if (endPage > safePages) {
    endPage = safePages;
    startPage = Math.max(1, endPage - windowSize + 1);
  }
  const pageNumbers = Array.from(
    { length: endPage - startPage + 1 },
    (_, i) => startPage + i
  );

  const goToPage = (targetPage: number) => {
    const clamped = Math.max(1, Math.min(safePages, targetPage));
    if (clamped === page) return;
    setPage(clamped);
    setLoading(true);
  };

  return (
    <div>
      {/* Sticky Header */}
      <header className="sticky top-0 z-10 bg-paper/80 backdrop-blur-md px-10 py-6">
        <h2 className="font-serif text-3xl font-bold text-dark mb-2">
          Manajemen Basis Pengetahuan
        </h2>
        <p className="font-body text-sm text-on-surface-variant font-medium">
          Database bahan-bahan TCM dan profil toksisitasnya
        </p>
      </header>

      <section className="px-10 pb-12">
        <div className="bg-white rounded-3xl overflow-hidden shadow-sm border border-light/50">

          {/* Search bar */}
          <div className="bg-light/10 px-8 py-4 flex justify-between items-center gap-4 border-b border-light/30">
            <div className="flex items-center gap-3 flex-1 max-w-md">
              <span className="material-symbols-outlined text-primary text-xl">
                search
              </span>
              <input
                id="ingredient-search"
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setLoading(true);
                }}
                placeholder="Cari nama Mandarin, Indonesia, atau Latin..."
                className="bg-transparent border-none focus:outline-none focus:ring-0 w-full font-body text-sm text-dark placeholder:text-on-surface-variant/50"
              />
            </div>
            <Link
              href="/admin/upload"
              className="flex items-center gap-2 text-white font-body font-bold text-xs bg-accent px-6 py-2.5 rounded-xl hover:brightness-105 transition-all whitespace-nowrap shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              Tambah Bahan
            </Link>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-light/5 border-b border-light/30 font-body">
                  <th className="px-8 py-5 text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                    NAMA BAHAN
                  </th>
                  <th className="px-8 py-5 text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                    NAMA LATIN
                  </th>
                  <th className="px-8 py-5 text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                    TERJEMAHAN
                  </th>
                  <th className="px-8 py-5 text-xs font-bold uppercase tracking-widest text-on-surface-variant text-right">
                    STATUS TOKSISITAS
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-light/30 font-body">
                {loading ? (
                  <tr>
                    <td colSpan={4} className="px-8 py-16 text-center text-sm text-on-surface-variant">
                      Memuat data...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-8 py-16 text-center text-sm text-on-surface-variant">
                      {search ? `Tidak ada hasil untuk "${search}"` : "Belum ada bahan dalam database."}
                    </td>
                  </tr>
                ) : (
                  filtered.map((ing) => {
                    const badge = getBadge(ing);
                    const firstChar = ing.mandarin_name.charAt(0) || "?";
                    return (
                      <tr key={ing._id} className="hover:bg-light/5 transition-colors group">
                        <td className="px-8 py-6">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-lg bg-light/30 flex items-center justify-center flex-shrink-0">
                              <span className="font-chinese text-primary font-bold text-lg leading-none">
                                {firstChar}
                              </span>
                            </div>
                            <div>
                              <p className="font-serif font-bold text-lg text-dark leading-tight">
                                {ing.mandarin_name}
                              </p>
                              <p className="text-xs text-on-surface-variant mt-0.5">
                                {ing.indonesian_name}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-8 py-6 text-sm text-on-surface-variant italic">
                          {ing.latin_name ?? "-"}
                        </td>
                        <td className="px-8 py-6 text-sm text-on-surface-variant">
                          {ing.english_name ?? "-"}
                        </td>
                        <td className="px-8 py-6 text-right">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${badge.className}`}>
                            {badge.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-8 py-6 border-t border-light/30 flex flex-wrap justify-between items-center gap-4 text-sm font-medium text-on-surface-variant font-body">
            <span>
              {loading
                ? "Memuat..."
                : `Menampilkan ${filtered.length} dari ${total.toLocaleString("id-ID")} bahan (Hal. ${page} dari ${safePages})`}
            </span>
            <div className="flex gap-1.5 items-center">
              <button
                type="button"
                onClick={() => goToPage(page - 1)}
                disabled={page <= 1 || loading}
                aria-label="Halaman sebelumnya"
                className="w-8 h-8 rounded flex items-center justify-center hover:bg-light/10 disabled:opacity-30 transition-colors cursor-pointer disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-sm">chevron_left</span>
              </button>
              {startPage > 1 && (
                <>
                  <button
                    type="button"
                    onClick={() => goToPage(1)}
                    className="w-8 h-8 rounded flex items-center justify-center text-xs font-bold hover:bg-light/20 text-on-surface-variant transition-colors cursor-pointer"
                  >
                    1
                  </button>
                  {startPage > 2 && (
                    <span className="px-1 text-xs text-on-surface-variant">…</span>
                  )}
                </>
              )}
              {pageNumbers.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => goToPage(p)}
                  aria-current={p === page ? "page" : undefined}
                  className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold transition-colors cursor-pointer ${
                    p === page ? "bg-primary text-white" : "hover:bg-light/20 text-on-surface-variant"
                  }`}
                >
                  {p}
                </button>
              ))}
              {endPage < safePages && (
                <>
                  {endPage < safePages - 1 && (
                    <span className="px-1 text-xs text-on-surface-variant">…</span>
                  )}
                  <button
                    type="button"
                    onClick={() => goToPage(safePages)}
                    className="w-8 h-8 rounded flex items-center justify-center text-xs font-bold hover:bg-light/20 text-on-surface-variant transition-colors cursor-pointer"
                  >
                    {safePages}
                  </button>
                </>
              )}
              <button
                type="button"
                onClick={() => goToPage(page + 1)}
                disabled={page >= safePages || loading}
                aria-label="Halaman berikutnya"
                className="w-8 h-8 rounded flex items-center justify-center hover:bg-light/10 disabled:opacity-30 transition-colors cursor-pointer disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-sm">chevron_right</span>
              </button>
            </div>
          </div>

        </div>
      </section>
    </div>
  );
}
