"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { adminLogin, setToken } from "@/lib/adminApi";

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
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div className="w-full max-w-sm">

        {/* Brand — matches sidebar brand style */}
        <div className="text-center mb-10">
          <h1 className="font-serif text-4xl font-bold text-primary italic">
            FitMate
          </h1>
          <p className="font-sans text-xs uppercase tracking-widest text-on-surface-variant mt-2">
            Admin Console
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-surface-container-low rounded-3xl p-8 shadow-ambient">
          <h2 className="font-serif text-xl text-on-surface mb-6">
            Masuk ke Dasbor
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div>
              <label htmlFor="admin-username" className="font-sans text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                Username
              </label>
              <input
                id="admin-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-2 w-full bg-surface-container px-4 py-3 rounded-xl font-sans text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-surface-container-high transition-all"
                placeholder="admin"
                required
                autoComplete="username"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="admin-password" className="font-sans text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                Password
              </label>
              <input
                id="admin-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-2 w-full bg-surface-container px-4 py-3 rounded-xl font-sans text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-surface-container-high transition-all"
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="bg-error-container rounded-xl px-4 py-3 flex items-start gap-2">
                <span className="material-symbols-outlined text-error text-sm mt-0.5">
                  error
                </span>
                <p className="font-sans text-sm text-error">{error}</p>
              </div>
            )}

            {/* Submit — Gold CTA per design system */}
            <button
              id="admin-login-submit"
              type="submit"
              disabled={loading}
              className="w-full py-3 px-6 rounded-xl bg-tertiary-container text-on-tertiary-fixed font-sans font-bold text-sm hover:brightness-105 active:scale-95 transition-all disabled:opacity-60 mt-2"
            >
              {loading ? "Memverifikasi..." : "Masuk"}
            </button>
          </form>
        </div>

        <p className="text-center font-sans text-xs text-on-surface-variant mt-8 opacity-60">
          FitMate TCM Safety Scanner — Admin Portal
        </p>
      </div>
    </div>
  );
}
