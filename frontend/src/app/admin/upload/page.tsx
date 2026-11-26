"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  validateUploadFile,
  importUploadFile,
  ValidationResult,
  ImportResult,
} from "@/lib/adminApi";

type UploadState =
  | "idle"
  | "validating"
  | "validated"
  | "importing"
  | "done"
  | "error";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const router = useRouter();

  const handleValidate = useCallback(
    async (uploadedFile: File) => {
      setUploadState("validating");
      setValidation(null);
      setImportResult(null);
      setErrorMsg("");

      try {
        const data = await validateUploadFile(uploadedFile);
        setValidation(data);
        setUploadState("validated");
      } catch (err: unknown) {
        if (err instanceof Error && err.message === "Unauthorized") {
          router.replace("/admin/login");
          return;
        }
        setErrorMsg(
          err instanceof Error
            ? err.message
            : "Terjadi kesalahan saat validasi"
        );
        setUploadState("error");
      }
    },
    [router]
  );

  const handleImport = async () => {
    if (!file || !validation || validation.error_count > 0) return;
    setUploadState("importing");

    try {
      const data = await importUploadFile(file);
      setImportResult(data);
      setUploadState("done");
    } catch (err: unknown) {
      if (err instanceof Error && err.message === "Unauthorized") {
        router.replace("/admin/login");
        return;
      }
      setErrorMsg(err instanceof Error ? err.message : "Impor gagal");
      setUploadState("error");
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
      maxSize: 10 * 1024 * 1024,
      maxFiles: 1,
      disabled: uploadState === "validating" || uploadState === "importing",
    });

  const isWorking =
    uploadState === "validating" || uploadState === "importing";

  return (
    <div className="bg-paper min-h-full">
      {/* Sticky Header */}
      <header className="sticky top-0 z-10 bg-paper/90 backdrop-blur-md border-b border-line px-6 md:px-10 py-6">
        <h2 className="font-serif text-3xl font-bold text-primary italic">
          Unggah Data Excel
        </h2>
        <p className="font-sans text-sm text-ink-soft mt-1">
          Impor bahan TCM tervalidasi dari file Excel atau CSV
        </p>
      </header>

      <section className="px-6 md:px-10 pb-20 lg:pb-12 max-w-3xl">
        {/* Drop Zone */}
        <div
          {...getRootProps()}
          className={`mt-8 rounded-3xl border-2 border-dashed p-12 text-center cursor-pointer transition-all select-none ${
            isDragActive
              ? "border-trust bg-trust-tint scale-[1.01]"
              : isWorking
              ? "border-line bg-paper-deep cursor-not-allowed opacity-60"
              : "border-line bg-card hover:border-trust hover:bg-trust-tint/40"
          }`}
        >
          <input {...getInputProps()} />
          <span className="material-symbols-outlined text-5xl text-primary opacity-60 mb-4 block">
            upload_file
          </span>
          {isDragActive ? (
            <p className="font-sans font-semibold text-trust-deep">
              Lepaskan file di sini...
            </p>
          ) : uploadState === "validating" ? (
            <p className="font-sans text-ink-soft">Memvalidasi file...</p>
          ) : uploadState === "importing" ? (
            <p className="font-sans text-ink-soft">
              Mengimpor data ke database...
            </p>
          ) : (
            <>
              <p className="font-sans font-semibold text-ink">
                Seret dan lepas file Excel atau CSV ke sini
              </p>
              <p className="font-sans text-sm text-ink-soft mt-2">
                atau klik untuk memilih file
              </p>
              <p className="font-sans text-xs text-ink-faint mt-4">
                Format: .xlsx, .csv (Maks. 10MB)
              </p>
            </>
          )}
        </div>

        {/* File rejection errors (wrong type / too large) */}
        {fileRejections.length > 0 && (
          <div className="mt-4 bg-danger-tint border border-danger/30 rounded-2xl px-5 py-4">
            {fileRejections[0].errors.map((e) => (
              <p key={e.code} className="font-sans text-sm text-danger-deep">
                {e.message}
              </p>
            ))}
          </div>
        )}

        {/* Error state */}
        {uploadState === "error" && (
          <div
            role="alert"
            className="mt-6 bg-danger-tint border border-danger/30 rounded-2xl px-6 py-4 flex items-start gap-3"
          >
            <span className="material-symbols-outlined text-danger flex-shrink-0 mt-0.5">
              error
            </span>
            <div>
              <p className="font-sans font-semibold text-danger-deep">
                Terjadi Kesalahan
              </p>
              <p className="font-sans text-sm text-danger-deep/90 mt-1">
                {errorMsg}
              </p>
              <button
                type="button"
                onClick={handleReset}
                className="mt-3 font-sans text-xs font-semibold text-danger-deep underline cursor-pointer"
              >
                Coba lagi
              </button>
            </div>
          </div>
        )}

        {/* Validation Result */}
        {validation && uploadState !== "done" && (
          <div className="mt-8 bg-card border border-line rounded-3xl overflow-hidden shadow-xs">
            {/* Summary */}
            <div className="px-8 py-6 border-b border-line flex justify-between items-center">
              <div>
                <p className="font-sans text-xs uppercase tracking-wider text-ink-soft">
                  FILE
                </p>
                <p className="font-sans font-semibold text-ink mt-1">
                  {validation.filename}
                </p>
              </div>
              <div className="text-right">
                <p className="font-sans text-xs uppercase tracking-wider text-ink-soft">
                  TOTAL BARIS
                </p>
                <p className="font-serif text-2xl font-bold text-ink mt-1">
                  {validation.total_rows}
                </p>
              </div>
            </div>

            {/* Counts */}
            <div className="grid grid-cols-2 divide-x divide-line">
              <div className="px-8 py-6">
                <p className="font-sans text-xs uppercase tracking-wider text-ink-soft">
                  SIAP DIIMPOR
                </p>
                <p className="font-serif text-3xl font-bold text-trust-deep mt-2">
                  {validation.valid_count}
                </p>
              </div>
              <div className="px-8 py-6">
                <p className="font-sans text-xs uppercase tracking-wider text-ink-soft">
                  BARIS BERMASALAH
                </p>
                <p
                  className={`font-serif text-3xl font-bold mt-2 ${
                    validation.error_count > 0 ? "text-danger" : "text-ink"
                  }`}
                >
                  {validation.error_count}
                </p>
              </div>
            </div>

            {/* Row-level errors */}
            {validation.error_count > 0 && (
              <div className="px-8 pb-6">
                <p className="font-sans text-sm font-semibold text-danger-deep mb-3">
                  Perbaiki baris berikut dan unggah ulang:
                </p>
                <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
                  {validation.errors.map((err) => (
                    <div
                      key={err.row}
                      className="bg-paper-deep border border-line rounded-2xl px-4 py-3"
                    >
                      <p className="font-sans text-xs font-bold uppercase tracking-wider text-ink-soft">
                        Baris {err.row}
                      </p>
                      <ul className="mt-1 space-y-1">
                        {err.errors.map((e, i) => (
                          <li
                            key={i}
                            className="font-sans text-sm text-danger-deep"
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
            <div className="px-8 py-5 border-t border-line bg-paper/50 flex gap-4 flex-wrap">
              <button
                type="button"
                onClick={handleReset}
                className="px-6 py-2.5 rounded-xl bg-paper-deep border border-line text-ink font-sans font-semibold text-sm hover:bg-paper transition-all active:scale-95 cursor-pointer"
              >
                Ganti File
              </button>
              {/* Confirm import: ONLY shows when zero errors */}
              {validation.error_count === 0 && (
                <button
                  id="confirm-import-btn"
                  type="button"
                  onClick={handleImport}
                  disabled={uploadState === "importing"}
                  className="px-8 py-2.5 rounded-xl bg-trust hover:bg-trust-deep text-white font-sans font-bold text-sm shadow-xs active:scale-95 transition-all disabled:opacity-60 cursor-pointer"
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
          <div className="mt-8 bg-card border border-line rounded-3xl px-8 py-8 shadow-xs">
            <div className="flex items-center gap-4 mb-6">
              <span
                className="material-symbols-outlined text-4xl text-trust"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                check_circle
              </span>
              <div>
                <h3 className="font-serif text-xl font-bold text-ink">
                  Impor Berhasil
                </h3>
                <p className="font-sans text-sm text-ink-soft mt-1">
                  {importResult.message}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-paper-deep border border-line rounded-2xl px-6 py-4">
                <p className="font-sans text-xs uppercase tracking-wider text-ink-soft">
                  BAHAN BARU
                </p>
                <p className="font-serif text-3xl font-bold text-trust-deep mt-1">
                  {importResult.imported}
                </p>
              </div>
              <div className="bg-paper-deep border border-line rounded-2xl px-6 py-4">
                <p className="font-sans text-xs uppercase tracking-wider text-ink-soft">
                  DIPERBARUI
                </p>
                <p className="font-serif text-3xl font-bold text-ink mt-1">
                  {importResult.updated}
                </p>
              </div>
            </div>
            <div className="flex gap-4 flex-wrap">
              <button
                type="button"
                onClick={handleReset}
                className="px-6 py-2.5 rounded-xl bg-paper-deep border border-line text-ink font-sans font-semibold text-sm hover:bg-paper transition-all cursor-pointer"
              >
                Unggah File Lain
              </button>
              <Link
                href="/admin/ingredients"
                className="px-8 py-2.5 rounded-xl bg-trust hover:bg-trust-deep text-white font-sans font-bold text-sm transition-all"
              >
                Lihat Daftar Bahan
              </Link>
            </div>
          </div>
        )}

        {/* Usage Instructions: shown only when idle */}
        {uploadState === "idle" && (
          <div className="mt-8 bg-card border border-line rounded-3xl px-8 py-6 shadow-xs">
            <h3 className="font-serif text-lg font-bold text-ink mb-4">
              Format File yang Diperlukan
            </h3>
            <p className="font-sans text-sm text-ink-soft mb-3">
              File Excel/CSV harus memiliki header di baris pertama:
            </p>
            <div className="bg-paper-deep border border-line rounded-2xl px-4 py-3 overflow-x-auto">
              <code className="font-mono text-xs text-ink">
                mandarin_name | indonesian_name | is_toxic | source_reference | ...
              </code>
            </div>
            <p className="font-sans text-xs text-ink-soft mt-3">
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
