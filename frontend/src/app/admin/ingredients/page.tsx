"use client";

import { useState, useEffect } from "react";
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
    className: "bg-error-container text-error",
  },
  moderate: {
    label: "Sedang",
    className: "bg-tertiary-container text-on-tertiary-fixed",
  },
  low: {
    label: "Rendah",
    className: "bg-surface-container text-on-surface-variant",
  },
  unknown: {
    label: "Tidak Diketahui",
    className: "bg-surface-container text-on-surface-variant",
  },
};

const SAFE_BADGE: BadgeConfig = {
  label: "Aman",
  className: "bg-surface-container-low text-on-surface-variant",
};

export default function IngredientsPage() {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const router = useRouter();

  useEffect(() => {
    setLoading(true);
    getIngredients(page, 20)
      .then((data: { ingredients: Ingredient[]; total: number; pages: number }) => {
        setIngredients(data.ingredients);
        setTotal(data.total);
        setPages(data.pages);
      })
      .catch((err: Error) => {
        if (err.message === "Unauthorized") router.replace("/admin/login");
      })
      .finally(() => setLoading(false));
  }, [page, router]);

  const filtered = ingredients.filter((ing) =>
    search === "" ||
    ing.mandarin_name.includes(search) ||
    ing.indonesian_name.toLowerCase().includes(search.toLowerCase()) ||
    (ing.latin_name ?? "").toLowerCase().includes(search.toLowerCase())
  );

  const getBadge = (ing: Ingredient): BadgeConfig => {
    if (!ing.is_toxic) return SAFE_BADGE;
    return TOXICITY_BADGES[ing.toxicity_level ?? "unknown"] ?? TOXICITY_BADGES.unknown;
  };

  const pageNumbers = Array.from(
    { length: Math.min(pages, 5) },
    (_, i) => i + 1
  );

  return (
    <div>
      {/* Sticky Header */}
      <header className="sticky top-0 z-10 bg-surface/80 backdrop-blur-md px-10 py-6">
        <h2 className="font-headline text-3xl font-bold text-dark mb-2">
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
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cari nama Mandarin, Indonesia, atau Latin..."
                className="bg-transparent border-none focus:outline-none focus:ring-0 w-full font-body text-sm text-dark placeholder:text-on-surface-variant/50"
              />
            </div>
            <a
              href="/admin/upload"
              className="flex items-center gap-2 text-white font-body font-bold text-xs bg-accent px-6 py-2.5 rounded-xl hover:brightness-105 transition-all whitespace-nowrap shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              Tambah Bahan
            </a>
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
                              <p className="font-headline font-bold text-lg text-dark leading-tight">
                                {ing.mandarin_name}
                              </p>
                              <p className="text-xs text-on-surface-variant mt-0.5">
                                {ing.indonesian_name}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-8 py-6 text-sm text-on-surface-variant italic">
                          {ing.latin_name ?? "—"}
                        </td>
                        <td className="px-8 py-6 text-sm text-on-surface-variant">
                          {ing.english_name ?? "—"}
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
          <div className="px-8 py-6 border-t border-light/30 flex justify-between items-center text-sm font-medium text-on-surface-variant font-body">
            <span>
              {loading ? "Memuat..." : `Menampilkan ${filtered.length} dari ${total} bahan`}
            </span>
            <div className="flex gap-2 items-center">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="w-8 h-8 rounded flex items-center justify-center hover:bg-light/10 disabled:opacity-30 transition-colors"
              >
                <span className="material-symbols-outlined text-sm">chevron_left</span>
              </button>
              {pageNumbers.map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold transition-colors ${
                    p === page ? "bg-primary text-white" : "hover:bg-light/20 text-on-surface-variant"
                  }`}
                >
                  {p}
                </button>
              ))}
              <button
                onClick={() => setPage(Math.min(pages, page + 1))}
                disabled={page === pages}
                className="w-8 h-8 rounded flex items-center justify-center hover:bg-light/10 disabled:opacity-30 transition-colors"
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
