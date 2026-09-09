"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { adminLogin, setToken } from "@/lib/adminApi";
import Link from "next/link";

export default function AdminLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const token = await adminLogin(username, password);
      setToken(token);
      router.replace("/admin");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login gagal";
      setError(message || "Periksa username dan password Anda.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-sm mx-auto">
      {/* Brandmark */}
      <div className="text-center mb-8">
        <Link
          href="/"
          className="font-serif text-3xl font-bold text-heritage italic hover:opacity-90 transition-opacity inline-block"
        >
          FitMate TCM
        </Link>
        <p className="text-[11px] uppercase tracking-widest text-ink-faint mt-1.5 font-semibold">
          Admin Console
        </p>
      </div>

      {/* Login Card */}
      <div className="bg-card rounded-[20px] p-7 border border-line shadow-[0_20px_40px_-20px_rgba(33,28,23,0.15)]">
        <h2 className="font-serif text-xl font-bold text-ink mb-5">
          Masuk ke Dasbor
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username */}
          <div>
            <label
              htmlFor="admin-username"
              className="block text-[11px] font-bold uppercase tracking-wider text-ink-soft mb-1.5"
            >
              Username
            </label>
            <input
              id="admin-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              placeholder="admin"
              className="w-full bg-paper border border-line rounded-[10px] px-3.5 py-2.5 text-[13.5px] text-ink focus:outline-none focus:border-trust transition-colors placeholder:text-ink-faint"
            />
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="admin-password"
              className="block text-[11px] font-bold uppercase tracking-wider text-ink-soft mb-1.5"
            >
              Password
            </label>
            <input
              id="admin-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className="w-full bg-paper border border-line rounded-[10px] px-3.5 py-2.5 text-[13.5px] text-ink focus:outline-none focus:border-trust transition-colors placeholder:text-ink-faint"
            />
          </div>

          {error && (
            <div className="p-3 bg-danger-tint border border-danger/30 rounded-[10px] text-danger text-[12px] leading-tight">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 bg-trust hover:bg-trust-deep text-white font-semibold text-[13px] rounded-[10px] shadow-sm transition-colors active:scale-95 disabled:opacity-60 cursor-pointer"
          >
            {loading ? "Memverifikasi..." : "Masuk"}
          </button>
        </form>

        <div className="text-center mt-5 pt-4 border-t border-line/60">
          <Link
            href="/"
            className="text-[12px] text-ink-soft hover:text-ink transition-colors font-medium"
          >
            ← Kembali ke Halaman Utama
          </Link>
        </div>
      </div>
    </div>
  );
}
