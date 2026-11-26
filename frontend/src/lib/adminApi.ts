/**
 * adminApi.ts: Utility functions for all admin API calls.
 * All protected calls automatically attach the JWT from localStorage.
 *
 * Security note (prototype): JWT stored in localStorage is XSS-vulnerable.
 * Post-PIMNAS: migrate to httpOnly cookies + refresh token rotation.
 */

import { getApiBaseUrl } from "./apiConfig";

const getBase = () => getApiBaseUrl();

export interface RowError {
  field: string;
  message: string;
}

export interface ValidationError {
  row: number;
  errors: RowError[];
}

export interface ValidationResult {
  total_rows: number;
  valid_count: number;
  error_count: number;
  errors: ValidationError[];
  filename: string;
}

export interface ImportResult {
  success: boolean;
  imported: number;
  updated: number;
  failed: number;
  message: string;
}

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

/**
 * Normalizes an RFC 7515 Base64URL segment to standard Base64 with '=' padding.
 */
function base64UrlToBase64(segment: string): string {
  const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
  const remainder = base64.length % 4;
  if (remainder === 2) return `${base64}==`;
  if (remainder === 3) return `${base64}=`;
  if (remainder === 1) throw new Error("Invalid Base64URL length");
  return base64;
}

export function isTokenExpired(token: string): boolean {
  try {
    const parts = token.split(".");
    if (parts.length !== 3 || !parts[1]) return true;
    const normalized = base64UrlToBase64(parts[1]);
    const payload = JSON.parse(atob(normalized)) as { exp?: unknown };
    if (typeof payload.exp !== "number") return true;
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

function adminHeaders(): HeadersInit {
  const token = getToken();
  if (token && isTokenExpired(token)) {
    clearToken();
    return { "Content-Type": "application/json" };
  }
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function getValidAuthHeader(): HeadersInit {
  const token = getToken();
  if (!token || isTokenExpired(token)) {
    clearToken();
    throw new Error("Unauthorized");
  }
  return { Authorization: `Bearer ${token}` };
}

export async function adminLogin(
  username: string,
  password: string
): Promise<string> {
  const res = await fetch(`${getBase()}/api/v1/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Login gagal");
  }
  const data = await res.json();
  return data.access_token;
}

export async function getAdminStats() {
  const res = await fetch(`${getBase()}/api/v1/admin/stats`, {
    headers: adminHeaders(),
    signal: AbortSignal.timeout(10000),
  });
  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error("Gagal mengambil statistik");
  return res.json();
}

export async function getIngredients(page = 1, limit = 20, search = "") {
  const queryParam = search ? `&q=${encodeURIComponent(search)}` : "";
  const res = await fetch(
    `${getBase()}/api/v1/admin/ingredients?page=${page}&limit=${limit}${queryParam}`,
    {
      headers: adminHeaders(),
      signal: AbortSignal.timeout(10000),
    }
  );
  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error("Gagal mengambil daftar bahan");
  return res.json();
}

export async function validateUploadFile(file: File): Promise<ValidationResult> {
  const headers = getValidAuthHeader();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${getBase()}/api/v1/admin/upload/validate`, {
    method: "POST",
    headers,
    body: formData,
    signal: AbortSignal.timeout(30000),
  });

  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Validasi gagal");
  }
  return res.json();
}

export async function importUploadFile(file: File): Promise<ImportResult> {
  const headers = getValidAuthHeader();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${getBase()}/api/v1/admin/upload/import`, {
    method: "POST",
    headers,
    body: formData,
    signal: AbortSignal.timeout(30000),
  });

  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Impor gagal");
  }
  return res.json();
}
