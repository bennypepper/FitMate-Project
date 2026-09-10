"use client";

import { useState, useEffect } from "react";
import { getAdminStats } from "@/lib/adminApi";
import { useRouter } from "next/navigation";
import Link from "next/link";

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
      .then((data) => {
        setStats(data);
      })
      .catch((err: Error) => {
        if (err.message === "Unauthorized") {
          router.replace("/admin/login");
        }
      })
      .finally(() => setLoading(false));
  }, [router]);

  const fmt = (n: number | undefined) =>
    n !== undefined ? n.toLocaleString("id-ID") : "0";

  // Mock recent scan activity log matching mockup
  const recentActivities = [
    {
      time: "08:42",
      herb: "轻粉 · Qing Fen (Merkuri klorida)",
      status: "Berisiko",
      isRisk: true,
      source: "Kamera HP",
    },
    {
      time: "08:15",
      herb: "当归 · Dang Gui (Dong Quai)",
      status: "Aman",
      isRisk: false,
      source: "Unggah galeri",
    },
    {
      time: "07:53",
      herb: "甘草 · Gan Cao (Licorice)",
      status: "Aman",
      isRisk: false,
      source: "Kamera HP",
    },
    {
      time: "Kemarin",
      herb: "金嗓子喉片 · Golden Throat",
      status: "Aman",
      isRisk: false,
      source: "Kamera HP",
    },
    {
      time: "Kemarin",
      herb: "附子 · Fu Zi (Aconite Root)",
      status: "Berisiko",
      isRisk: true,
      source: "Unggah galeri",
    },
  ];

  const handleExportReport = () => {
    const csvContent =
      "Waktu,Bahan Terdeteksi,Status,Sumber\n" +
      recentActivities
        .map((a) => `"${a.time}","${a.herb}","${a.status}","${a.source}"`)
        .join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `laporan_skrining_fitmate_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6 md:p-8 lg:p-9 max-w-[1100px] w-full mx-auto">
      {/* Admin Head (Mockup Header) */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-7">
        <div>
          <h1 className="font-serif font-bold text-[24px] text-ink mb-1">
            Analitik Pemindaian
          </h1>
          <p className="text-[13px] text-ink-soft">
            Tinjauan klinis penyaringan keamanan bahan.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-2 bg-card border border-line px-3.5 py-2 rounded-[10px] text-[12.5px] font-semibold text-ink shadow-xs">
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
            >
              <rect x="3" y="4" width="18" height="18" rx="2" />
              <path d="M16 2v4M8 2v4M3 10h18" />
            </svg>
            <span>30 hari terakhir</span>
            <svg
              width="11"
              height="11"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </div>

          <button
            onClick={handleExportReport}
            className="px-4 py-2 bg-transparent text-trust-deep hover:bg-trust-tint border border-trust font-semibold text-[13px] rounded-[10px] transition-colors flex items-center gap-2 cursor-pointer active:scale-95"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <path d="M12 15V3" />
            </svg>
            Ekspor Laporan
          </button>
        </div>
      </div>

      {/* KPI Row (3 Cards: Neutral, Danger Highlight, Safe) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-7">
        
        {/* KPI 1: Total Bahan (Neutral) */}
        <div className="bg-card border border-line rounded-[14px] p-5 relative overflow-hidden shadow-xs">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-ink-faint" />
          <div className="flex justify-between items-start mb-3.5">
            <span className="text-[11px] font-bold tracking-wider text-ink-soft uppercase">
              Total Bahan
            </span>
            <div className="w-[30px] h-[30px] rounded-[8px] bg-paper-deep text-ink-soft flex items-center justify-center">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 3v18h18" />
                <rect x="7" y="12" width="3" height="6" />
                <rect x="12" y="8" width="3" height="10" />
                <rect x="17" y="5" width="3" height="13" />
              </svg>
            </div>
          </div>
          <div className="font-bold text-[32px] text-ink tabular-nums">
            {loading ? "..." : fmt(stats?.total_ingredients)}
          </div>
          <div className="text-[11.5px] text-ink-faint mt-1.5">
            {stats?.total_ingredients ? "Dataset terindeks di memori server" : "Belum ada data: silakan unggah dataset"}
          </div>
        </div>

        {/* KPI 2: Bahan Toksik (DANGER: Menyalakan Merah!) */}
        <div className="bg-danger-tint border border-danger/30 rounded-[14px] p-5 relative overflow-hidden shadow-xs">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-danger" />
          <div className="flex justify-between items-start mb-3.5">
            <span className="text-[11px] font-bold tracking-wider text-danger-deep uppercase">
              Bahan Toksik
            </span>
            <div className="w-[30px] h-[30px] rounded-[8px] bg-danger text-white flex items-center justify-center shadow-xs">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4">
                <path d="M12 9v4M12 17h.01M10.3 3.9L2.5 17a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
              </svg>
            </div>
          </div>
          <div className="font-bold text-[32px] text-danger-deep tabular-nums">
            {loading ? "..." : fmt(stats?.toxic_count)}
          </div>
          <div className="text-[11.5px] text-danger-deep/80 mt-1.5">
            {stats?.toxic_count && stats.toxic_count > 0
              ? `${stats.toxic_count} bahan berisiko terdaftar di filter aktif`
              : "Akan menyala saat bahan berisiko terdeteksi"}
          </div>
        </div>

        {/* KPI 3: Bahan Aman (Safe) */}
        <div className="bg-card border border-line rounded-[14px] p-5 relative overflow-hidden shadow-xs">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-trust" />
          <div className="flex justify-between items-start mb-3.5">
            <span className="text-[11px] font-bold tracking-wider text-ink-soft uppercase">
              Bahan Aman
            </span>
            <div className="w-[30px] h-[30px] rounded-[8px] bg-trust-tint text-trust-deep flex items-center justify-center">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5z" />
              </svg>
            </div>
          </div>
          <div className="font-bold text-[32px] text-ink tabular-nums">
            {loading ? "..." : fmt(stats?.safe_count)}
          </div>
          <div className="text-[11.5px] text-ink-faint mt-1.5">
            Terverifikasi terhadap basis data apoteker
          </div>
        </div>

      </div>

      {/* Shortcuts Management Section */}
      <div className="mb-7">
        <h3 className="font-serif font-bold text-[16.5px] text-ink mb-1">
          Pintasan Manajemen
        </h3>
        <p className="text-[12.5px] text-ink-soft mb-3.5">
          Akses cepat ke menu administrasi
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link
            href="/admin/ingredients"
            className="bg-card border border-line rounded-[14px] p-4.5 flex gap-3.5 items-start hover:border-trust transition-colors group shadow-xs"
          >
            <div className="w-[38px] h-[38px] rounded-[10px] bg-trust-tint text-trust-deep flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 6h16M4 12h16M4 18h10" />
              </svg>
            </div>
            <div>
              <h5 className="text-[13.5px] font-semibold text-ink mb-1 group-hover:text-trust transition-colors">
                Daftar Bahan
              </h5>
              <p className="text-[12px] text-ink-soft leading-normal">
                Lihat semua bahan TCM dan status toksisitasnya
              </p>
            </div>
          </Link>

          <Link
            href="/admin/upload"
            className="bg-card border border-line rounded-[14px] p-4.5 flex gap-3.5 items-start hover:border-amber transition-colors group shadow-xs"
          >
            <div className="w-[38px] h-[38px] rounded-[10px] bg-amber-tint text-amber flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 3v13" />
                <path d="M7 8l5-5 5 5" />
                <path d="M4 17v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
              </svg>
            </div>
            <div>
              <h5 className="text-[13.5px] font-semibold text-ink mb-1 group-hover:text-amber transition-colors">
                Unggah Data Excel
              </h5>
              <p className="text-[12px] text-ink-soft leading-normal">
                Impor bahan tervalidasi dari file Excel atau CSV
              </p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div>
        <h3 className="font-serif font-bold text-[16.5px] text-ink mb-1">
          Aktivitas Terbaru
        </h3>
        <p className="text-[12.5px] text-ink-soft mb-3.5">
          Pemindaian terakhir dari pengguna
        </p>

        <div className="bg-card border border-line rounded-[14px] overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-line bg-paper/50">
                  <th className="py-3 px-4 text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                    Waktu
                  </th>
                  <th className="py-3 px-4 text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                    Bahan Terdeteksi
                  </th>
                  <th className="py-3 px-4 text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                    Status
                  </th>
                  <th className="py-3 px-4 text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                    Sumber
                  </th>
                </tr>
              </thead>
              <tbody>
                {recentActivities.map((act, idx) => (
                  <tr
                    key={idx}
                    className={`border-b border-line last:border-b-0 transition-colors ${
                      act.isRisk ? "bg-danger-tint/60" : "hover:bg-paper/40"
                    }`}
                  >
                    <td className="py-3 px-4 text-[13px] text-ink-soft font-mono text-xs">
                      {act.time}
                    </td>
                    <td className="py-3 px-4 text-[13px] text-ink font-medium">
                      {act.herb}
                    </td>
                    <td className="py-3 px-4 text-[13px]">
                      {act.isRisk ? (
                        <span className="inline-block text-[10.5px] font-bold px-2.5 py-0.5 rounded-full bg-danger text-white shadow-xs">
                          Berisiko
                        </span>
                      ) : (
                        <span className="inline-block text-[10.5px] font-bold px-2.5 py-0.5 rounded-full bg-trust-tint text-trust-deep border border-trust/20">
                          Aman
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[13px] text-ink-soft text-xs">
                      {act.source}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
