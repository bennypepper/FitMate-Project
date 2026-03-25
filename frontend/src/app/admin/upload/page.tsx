"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useRouter } from "next/navigation";
import { getToken, clearToken } from "@/lib/adminApi";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RowError {
  field: string;
  message: string;
}

interface ValidationError {
  row: number;
  errors: RowError[];
}

interface ValidationResult {
  total_rows: number;
  valid_count: number;
  error_count: number;
  errors: ValidationError[];
  filename: string;
}

interface ImportResult {
  success: boolean;
  imported: number;
  updated: number;
  failed: number;
  message: string;
}

type UploadState = "idle" | "validating" | "validated" | "importing" | "done" | "error";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const router = useRouter();

  const adminFetch = async (url: string, body: FormData): Promise<Response> => {
    const token = getToken();
    if (!token) {
      clearToken();
      router.replace("/admin/login");
      throw new Error("Unauthorized");
    }
    const res = await fetch(url, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      // NO Content-Type header — browser sets multipart/form-data boundary
      body,
    });
    if (res.status === 401) {
      clearToken();
      router.replace("/admin/login");
      throw new Error("Unauthorized");
    }
    return res;
  };

  const handleValidate = useCallback(async (uploadedFile: File) => {
    setUploadState("validating");
    setValidation(null);
    setImportResult(null);
    setErrorMsg("");

    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);
      const res = await adminFetch(
        `${API_BASE}/api/v1/admin/upload/validate`,
        formData
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(
          (err as { detail?: string }).detail ?? "Validasi gagal"
        );
      }

      const data: ValidationResult = await res.json();
      setValidation(data);
      setUploadState("validated");
    } catch (err: unknown) {
      if ((err as Error).message !== "Unauthorized") {
        setErrorMsg(
          (err as Error).message ?? "Terjadi kesalahan saat validasi"
        );
        setUploadState("error");
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleImport = async () => {
    if (!file || !validation || validation.error_count > 0) return;
    setUploadState("importing");

    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await adminFetch(
        `${API_BASE}/api/v1/admin/upload/import`,
        formData
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(
          (err as { detail?: string }).detail ?? "Impor gagal"
        );
      }

      const data: ImportResult = await res.json();
      setImportResult(data);
      setUploadState("done");
    } catch (err: unknown) {
      if ((err as Error).message !== "Unauthorized") {
        setErrorMsg((err as Error).message ?? "Impor gagal");
        setUploadState("error");
      }
    }
  };

  const handleReset = () => {
    setFile(null);
    setValidation(null);
    setImportResult(null);
    setErrorMsg("");
    setUploadState("idle");
  };

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      const uploaded = acceptedFiles[0];
      setFile(uploaded);
      await handleValidate(uploaded);
    },
    [handleValidate]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } =
    useDropzone({
      onDrop,
      accept: {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
          ".xlsx",
        ],
        "text/csv": [".csv"],
        "application/csv": [".csv"],
      },
      maxSize: 10 * 1024 * 1024, // 10MB
      maxFiles: 1,
      disabled:
        uploadState === "validating" || uploadState === "importing",
    });

  const isWorking =
    uploadState === "validating" || uploadState === "importing";

  return (
    <div>
      {/* Sticky Header */}
      <header className="sticky top-0 z-10 bg-surface-container-lowest/80 backdrop-blur-md px-10 py-6">
        <h2 className="font-serif text-3xl font-bold text-primary italic">
          Unggah Data Excel
        </h2>
        <p className="font-sans text-sm text-on-surface-variant mt-1">
          Impor bahan TCM tervalidasi dari file Excel atau CSV
        </p>
      </header>

      <section className="px-10 pb-20 lg:pb-12 max-w-3xl">

        {/* Drop Zone */}
        <div
          {...getRootProps()}
          className={`mt-8 rounded-3xl border-2 border-dashed p-12 text-center cursor-pointer transition-all select-none ${
            isDragActive
              ? "border-primary bg-surface-container-low scale-[1.01]"
              : isWorking
              ? "border-surface-container bg-surface-container-lowest cursor-not-allowed opacity-60"
              : "border-surface-container-high bg-surface-container-lowest hover:border-primary hover:bg-surface-container-low"
          }`}
        >
          <input {...getInputProps()} />
          <span className="material-symbols-outlined text-5xl text-primary opacity-50 mb-4 block">
            upload_file
          </span>
          {isDragActive ? (
            <p className="font-sans font-semibold text-primary">
              Lepaskan file di sini...
            </p>
          ) : uploadState === "validating" ? (
            <p className="font-sans text-on-surface-variant">
              Memvalidasi file...
            </p>
          ) : uploadState === "importing" ? (
            <p className="font-sans text-on-surface-variant">
              Mengimpor data ke database...
            </p>
          ) : (
            <>
              <p className="font-sans font-semibold text-on-surface">
                Seret dan lepas file Excel atau CSV ke sini
              </p>
              <p className="font-sans text-sm text-on-surface-variant mt-2">
                atau klik untuk memilih file
              </p>
              <p className="font-sans text-xs text-on-surface-variant mt-4 opacity-50">
                Format: .xlsx, .csv — Maks. 10MB
              </p>
            </>
          )}
        </div>

        {/* File rejection errors (wrong type / too large) */}
        {fileRejections.length > 0 && (
          <div className="mt-4 bg-error-container rounded-2xl px-5 py-4">
            {fileRejections[0].errors.map((e) => (
              <p key={e.code} className="font-sans text-sm text-error">
                {e.message}
              </p>
            ))}
          </div>
        )}

        {/* Error state */}
        {uploadState === "error" && (
          <div className="mt-6 bg-error-container rounded-2xl px-6 py-4 flex items-start gap-3">
            <span className="material-symbols-outlined text-error flex-shrink-0 mt-0.5">
              error
            </span>
            <div>
              <p className="font-sans font-semibold text-error">
                Terjadi Kesalahan
              </p>
              <p className="font-sans text-sm text-error/80 mt-1">
                {errorMsg}
              </p>
              <button
                onClick={handleReset}
                className="mt-3 font-sans text-xs font-semibold text-error underline"
              >
                Coba lagi
              </button>
            </div>
          </div>
        )}

        {/* Validation Result */}
        {validation && uploadState !== "done" && (
          <div className="mt-8 bg-surface-container-low rounded-3xl overflow-hidden">
            {/* Summary */}
            <div className="px-8 py-6 border-b border-surface-container flex justify-between items-center">
              <div>
                <p className="font-sans text-xs uppercase tracking-wider text-on-surface-variant">
                  FILE
                </p>
                <p className="font-sans font-semibold text-on-surface mt-1">
                  {validation.filename}
                </p>
              </div>
              <div className="text-right">
                <p className="font-sans text-xs uppercase tracking-wider text-on-surface-variant">
                  TOTAL BARIS
                </p>
                <p className="font-serif text-2xl font-bold text-on-surface mt-1">
                  {validation.total_rows}
                </p>
              </div>
            </div>

            {/* Counts */}
            <div className="grid grid-cols-2 divide-x divide-surface-container">
              <div className="px-8 py-6">
                <p className="font-sans text-xs uppercase tracking-wider text-on-surface-variant">
                  SIAP DIIMPOR
                </p>
                <p className="font-serif text-3xl font-bold text-primary mt-2">
                  {validation.valid_count}
                </p>
              </div>
              <div className="px-8 py-6">
                <p className="font-sans text-xs uppercase tracking-wider text-on-surface-variant">
                  BARIS BERMASALAH
                </p>
                <p
                  className={`font-serif text-3xl font-bold mt-2 ${
                    validation.error_count > 0
                      ? "text-error"
                      : "text-on-surface"
                  }`}
                >
                  {validation.error_count}
                </p>
              </div>
            </div>

            {/* Row-level errors */}
            {validation.error_count > 0 && (
              <div className="px-8 pb-6">
                <p className="font-sans text-sm font-semibold text-error mb-3">
                  Perbaiki baris berikut dan unggah ulang:
                </p>
                <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
                  {validation.errors.map((err) => (
                    <div
                      key={err.row}
                      className="bg-surface-container rounded-2xl px-4 py-3"
                    >
                      <p className="font-sans text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                        Baris {err.row}
                      </p>
                      <ul className="mt-1 space-y-1">
                        {err.errors.map((e, i) => (
                          <li
                            key={i}
                            className="font-sans text-sm text-error"
                          >
                            <span className="font-semibold">{e.field}:</span>{" "}
                            {e.message}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="px-8 py-5 border-t border-surface-container flex gap-4 flex-wrap">
              <button
                onClick={handleReset}
                className="px-6 py-2.5 rounded-xl bg-surface-container text-on-surface font-sans font-semibold text-sm hover:bg-surface-container-high transition-all active:scale-95"
              >
                Ganti File
              </button>
              {/* Confirm import — ONLY shows when zero errors */}
              {validation.error_count === 0 && (
                <button
                  id="confirm-import-btn"
                  onClick={handleImport}
                  disabled={uploadState === "importing"}
                  className="px-8 py-2.5 rounded-xl bg-tertiary-container text-on-tertiary-fixed font-sans font-bold text-sm hover:brightness-105 active:scale-95 transition-all disabled:opacity-60"
                >
                  {uploadState === "importing"
                    ? "Mengimpor..."
                    : `Konfirmasi Import (${validation.valid_count} bahan)`}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Import Success */}
        {uploadState === "done" && importResult && (
          <div className="mt-8 bg-surface-container-low rounded-3xl px-8 py-8">
            <div className="flex items-center gap-4 mb-6">
              <span
                className="material-symbols-outlined text-4xl text-primary"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                check_circle
              </span>
              <div>
                <h3 className="font-serif text-xl font-bold text-on-surface">
                  Impor Berhasil
                </h3>
                <p className="font-sans text-sm text-on-surface-variant mt-1">
                  {importResult.message}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-surface-container rounded-2xl px-6 py-4">
                <p className="font-sans text-xs uppercase tracking-wider text-on-surface-variant">
                  BAHAN BARU
                </p>
                <p className="font-serif text-3xl font-bold text-primary mt-1">
                  {importResult.imported}
                </p>
              </div>
              <div className="bg-surface-container rounded-2xl px-6 py-4">
                <p className="font-sans text-xs uppercase tracking-wider text-on-surface-variant">
                  DIPERBARUI
                </p>
                <p className="font-serif text-3xl font-bold text-on-surface mt-1">
                  {importResult.updated}
                </p>
              </div>
            </div>
            <div className="flex gap-4 flex-wrap">
              <button
                onClick={handleReset}
                className="px-6 py-2.5 rounded-xl bg-surface-container text-on-surface font-sans font-semibold text-sm hover:bg-surface-container-high transition-all"
              >
                Unggah File Lain
              </button>
              <a
                href="/admin/ingredients"
                className="px-8 py-2.5 rounded-xl bg-primary text-white font-sans font-bold text-sm hover:brightness-110 transition-all"
              >
                Lihat Daftar Bahan
              </a>
            </div>
          </div>
        )}

        {/* Usage Instructions — shown only when idle */}
        {uploadState === "idle" && (
          <div className="mt-8 bg-surface-container-low rounded-3xl px-8 py-6">
            <h3 className="font-serif text-lg font-bold text-on-surface mb-4">
              Format File yang Diperlukan
            </h3>
            <p className="font-sans text-sm text-on-surface-variant mb-3">
              File Excel/CSV harus memiliki header di baris pertama:
            </p>
            <div className="bg-surface-container rounded-2xl px-4 py-3 overflow-x-auto">
              <code className="font-mono text-xs text-on-surface">
                mandarin_name | indonesian_name | is_toxic | source_reference | ...
              </code>
            </div>
            <p className="font-sans text-xs text-on-surface-variant mt-3">
              Kolom wajib:{" "}
              <strong>mandarin_name</strong>,{" "}
              <strong>indonesian_name</strong>,{" "}
              <strong>is_toxic</strong> (true/false),{" "}
              <strong>source_reference</strong>
            </p>
          </div>
        )}

      </section>
    </div>
  );
}
