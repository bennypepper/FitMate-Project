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
      <header className="sticky top-0 z-10 bg-surface/80 backdrop-blur-md px-10 py-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="font-headline text-3xl font-bold text-primary italic">
            Analitik Pemindaian
          </h2>
          <p className="font-body text-sm text-on-surface-variant mt-1">
            Tinjauan klinis penyaringan keamanan bahan.
          </p>
        </div>
        <div className="flex gap-4 items-center">
            <div className="hidden md:flex items-center gap-2 bg-light/30 px-4 py-2 rounded-full border border-light/50">
                <span className="material-symbols-outlined text-sm text-primary">calendar_today</span>
                <span className="text-xs font-semibold text-on-surface-variant uppercase">30 Hari Terakhir</span>
            </div>
            <button className="bg-primary text-white font-body px-6 py-2 rounded-xl font-semibold flex items-center gap-2 active:scale-95 transition-all hover:bg-primary-dark shadow-sm">
                <span className="material-symbols-outlined">download</span>
                Ekspor Laporan
            </button>
        </div>
      </header>

      <section className="px-10 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-12">
          {/* Primary stat card — Imperial Red */}
          <div className="bg-primary text-white p-6 rounded-3xl flex justify-between items-center shadow-lg col-span-1 lg:col-span-2">
            <div>
              <p className="font-body text-xs uppercase tracking-widest opacity-80">
                TOTAL BAHAN
              </p>
              <h4 className="font-headline text-4xl font-bold mt-2">
                {loading ? "—" : fmt(stats?.total_ingredients)}
              </h4>
            </div>
            <span
              className="material-symbols-outlined text-4xl opacity-40"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              medication
            </span>
          </div>

          <div className="bg-light/30 p-6 rounded-3xl flex justify-between items-center border border-light/50">
            <div>
              <p className="font-body text-xs uppercase tracking-widest text-on-surface-variant">
                BAHAN TOKSIK
              </p>
              <h4 className="font-headline text-4xl font-bold text-secondary mt-2">
                {loading ? "—" : fmt(stats?.toxic_count)}
              </h4>
            </div>
            <span className="material-symbols-outlined text-4xl text-secondary opacity-30">
              warning
            </span>
          </div>

          <div className="bg-white p-6 rounded-3xl flex justify-between items-center border border-light/50 shadow-sm">
            <div>
              <p className="font-body text-xs uppercase tracking-widest text-on-surface-variant">
                BAHAN AMAN
              </p>
              <h4 className="font-headline text-4xl font-bold text-dark mt-2">
                {loading ? "—" : fmt(stats?.safe_count)}
              </h4>
            </div>
            <span className="material-symbols-outlined text-4xl text-success opacity-30">
              verified
            </span>
          </div>
        </div>

        <div className="mb-6">
            <h3 className="text-2xl font-headline font-bold text-dark mb-2">Pintasan Manajemen</h3>
            <p className="text-on-surface-variant font-body text-sm">Akses cepat ke menu administrasi</p>
        </div>

        {/* Quick Action Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <a
            href="/admin/ingredients"
            className="bg-white rounded-3xl p-8 flex items-center gap-6 hover:bg-light/10 border border-light/50 transition-colors group shadow-sm"
          >
            <span className="material-symbols-outlined text-4xl text-primary opacity-50 group-hover:opacity-100 transition-opacity">
              list_alt
            </span>
            <div>
              <h3 className="font-headline text-xl font-bold text-dark mb-1">
                Daftar Bahan
              </h3>
              <p className="font-body text-sm text-on-surface-variant">
                Lihat semua bahan TCM dan status toksisitasnya
              </p>
            </div>
          </a>

          <a
            href="/admin/upload"
            className="bg-primary text-white rounded-3xl p-8 flex items-center gap-6 hover:brightness-105 transition-all group relative overflow-hidden shadow-lg border-b-4 border-primary-dark/20"
          >
            <span className="material-symbols-outlined text-4xl opacity-70 group-hover:opacity-100 transition-opacity flex-shrink-0 relative z-10">
              upload_file
            </span>
            <div className="relative z-10">
              <h3 className="font-headline text-xl font-bold mb-1">
                Unggah Data Excel
              </h3>
              <p className="font-body text-sm opacity-90">
                Impor bahan tervalidasi dari file Excel atau CSV
              </p>
            </div>
            {/* Decorative background icon */}
            <div className="absolute right-[-20px] bottom-[-30px] opacity-10 pointer-events-none group-hover:scale-110 transition-transform duration-500">
              <span
                className="material-symbols-outlined text-[140px]"
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
