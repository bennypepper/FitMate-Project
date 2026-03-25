/**
 * adminApi.ts — Utility functions for all admin API calls.
 * All protected calls automatically attach the JWT from localStorage.
 *
 * Security note (prototype): JWT stored in localStorage is XSS-vulnerable.
 * Post-PIMNAS: migrate to httpOnly cookies + refresh token rotation.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("admin_token");
}

export function clearToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("admin_token");
  }
}

export function setToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("admin_token", token);
  }
}

export function isTokenExpired(token: string): boolean {
  try {
    const payloadBase64 = token.split(".")[1];
    // atob decodes base64 — no jwt-decode dep needed
    const payload = JSON.parse(atob(payloadBase64));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true; // treat unparseable tokens as expired
  }
}

function adminHeaders(): HeadersInit {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function adminLogin(
  username: string,
  password: string
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Login gagal");
  }
  const data = await res.json();
  return data.access_token;
}

export async function getAdminStats() {
  const res = await fetch(`${API_BASE}/api/v1/admin/stats`, {
    headers: adminHeaders(),
  });
  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error("Gagal mengambil statistik");
  return res.json();
}

export async function getIngredients(page = 1, limit = 20) {
  const res = await fetch(
    `${API_BASE}/api/v1/admin/ingredients?page=${page}&limit=${limit}`,
    { headers: adminHeaders() }
  );
  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error("Gagal mengambil daftar bahan");
  return res.json();
}
