"use client";

import { useState, useEffect } from "react";
import { getAdminStats } from "@/lib/adminApi";
import { useRouter } from "next/navigation";

interface Stats {
  total_ingredients: number;
  toxic_count: number;
  safe_count: number;
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch((err: Error) => {
        if (err.message === "Unauthorized") router.replace("/admin/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  const fmt = (n: number | undefined) =>
    n !== undefined ? n.toLocaleString("id-ID") : "—";

  return (
    <div>
      {/* Sticky Header — glassmorphism per design system */}
      <header className="sticky top-0 z-10 bg-surface-container-lowest/80 backdrop-blur-md px-10 py-6 flex justify-between items-start">
        <div>
          <h2 className="font-serif text-3xl font-bold text-primary italic">
            Basis Pengetahuan
          </h2>
          <p className="font-sans text-sm text-on-surface-variant mt-1">
            Tinjauan database bahan TCM dan status toksisitas
          </p>
        </div>
      </header>

      <section className="px-10 py-8">

        {/* Stat Cards — matches stitch_pkm_ki_fitme_v1/dashboard_admin/code.html lines 152-174 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">

          {/* Primary stat card — Imperial Red */}
          <div className="bg-primary text-white p-6 rounded-3xl flex justify-between items-center shadow-ambient">
            <div>
              <p className="font-sans text-xs uppercase tracking-widest opacity-70">
                TOTAL BAHAN
              </p>
              <h4 className="font-serif text-4xl font-bold mt-1">
                {loading ? "—" : fmt(stats?.total_ingredients)}
              </h4>
            </div>
            <span
              className="material-symbols-outlined text-4xl opacity-30"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              medication
            </span>
          </div>

          {/* Toxic count card */}
          <div className="bg-surface-container p-6 rounded-3xl flex justify-between items-center">
            <div>
              <p className="font-sans text-xs uppercase tracking-widest text-on-surface-variant">
                BAHAN TOKSIK
              </p>
              <h4 className="font-serif text-4xl font-bold text-secondary mt-1">
                {loading ? "—" : fmt(stats?.toxic_count)}
              </h4>
            </div>
            <span className="material-symbols-outlined text-4xl text-secondary opacity-20">
              warning
            </span>
          </div>

          {/* Safe count card */}
          <div className="bg-surface-container-low p-6 rounded-3xl flex justify-between items-center">
            <div>
              <p className="font-sans text-xs uppercase tracking-widest text-on-surface-variant">
                BAHAN AMAN
              </p>
              <h4 className="font-serif text-4xl font-bold text-on-surface mt-1">
                {loading ? "—" : fmt(stats?.safe_count)}
              </h4>
            </div>
            <span className="material-symbols-outlined text-4xl text-on-surface-variant opacity-20">
              verified
            </span>
          </div>
        </div>

        {/* Quick Action Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <a
            href="/admin/ingredients"
            className="bg-surface-container-low rounded-3xl p-8 flex items-center gap-6 hover:bg-surface-container transition-colors group"
          >
            <span className="material-symbols-outlined text-4xl text-primary opacity-50 group-hover:opacity-100 transition-opacity">
              list_alt
            </span>
            <div>
              <h3 className="font-serif text-xl font-bold text-on-surface">
                Daftar Bahan
              </h3>
              <p className="font-sans text-sm text-on-surface-variant mt-1">
                Lihat semua bahan TCM dan status toksisitasnya
              </p>
            </div>
          </a>

          <a
            href="/admin/upload"
            className="bg-primary text-white rounded-3xl p-8 flex items-center gap-6 hover:brightness-105 transition-all group relative overflow-hidden"
          >
            <span className="material-symbols-outlined text-4xl opacity-70 group-hover:opacity-100 transition-opacity flex-shrink-0">
              upload_file
            </span>
            <div>
              <h3 className="font-serif text-xl font-bold">
                Unggah Data Excel
              </h3>
              <p className="font-sans text-sm opacity-70 mt-1">
                Impor bahan tervalidasi dari file Excel atau CSV
              </p>
            </div>
            {/* Decorative background icon */}
            <div className="absolute right-0 bottom-0 opacity-10 pointer-events-none">
              <span
                className="material-symbols-outlined text-[120px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                cloud_upload
              </span>
            </div>
          </a>
        </div>

      </section>
    </div>
  );
}
