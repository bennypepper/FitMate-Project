"use client";

import { useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import CameraViewfinder from "@/components/scanner/CameraViewfinder";
import ProcessingLoader from "@/components/scanner/ProcessingLoader";
import ResultsCard from "@/components/results/ResultsCard";
import QRCodeBridge from "@/components/scanner/QRCodeBridge";
import { getApiBaseUrl } from "@/lib/apiConfig";

function HomeContent() {
  const searchParams = useSearchParams();
  const sessionParam = searchParams.get("session");
  const [bridgeUploaded, setBridgeUploaded] = useState(false);
  const [bridgeUploading, setBridgeUploading] = useState(false);
  const [bridgeResults, setBridgeResults] = useState<any | null>(null);

  const [image, setImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<any | null>(null);
  const [networkError, setNetworkError] = useState<string | null>(null);
  const [showLiveCamera, setShowLiveCamera] = useState(false);
  const [showQrBridge, setShowQrBridge] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Send captured or uploaded image to backend for OCR + Safety Analysis
  const handleImageReady = async (base64: string) => {
    setImage(base64);
    setIsProcessing(true);
    setResults(null);
    setNetworkError(null);

    try {
      const resMsg = await fetch(base64);
      const blob = await resMsg.blob();

      const formData = new FormData();
      formData.append("file", blob, "scan.jpg");
      formData.append("user_id", "web_consumer");

      const apiUrl = getApiBaseUrl();
      const response = await fetch(`${apiUrl}/api/v1/analyze/`, {
        method: "POST",
        body: formData,
        signal: AbortSignal.timeout(45000),
      });

      if (!response.ok) {
        let detail = `Server error ${response.status}`;
        try {
          const errData = await response.json();
          detail = errData.detail || detail;
        } catch {}
        throw new Error(detail);
      }

      const data = await response.json();
      const sa = data.safety_analysis || {};
      const allIngredients = [
        ...(sa.toxic || []).map((i: any) => ({ ...i, category: "toxic", is_toxic: true })),
        ...(sa.contraindicated || []).map((i: any) => ({ ...i, category: "contraindicated", is_toxic: true })),
        ...(sa.safe || []).map((i: any) => ({ ...i, category: "safe", is_toxic: false })),
        ...(sa.unknown || []).map((i: any) => ({ ...i, category: "unknown", is_toxic: false })),
      ];

      setResults({
        ingredients: allIngredients,
        disclaimer: data.disclaimer || "",
        ocr_blocks: data.ocr_blocks || [],
      });
    } catch (error: any) {
      console.error("[Scan Error]", error);
      if (typeof navigator !== "undefined" && !navigator.onLine) {
        setNetworkError(
          "Tidak ada koneksi internet. Pastikan perangkat Anda terhubung ke internet."
        );
      } else {
        setNetworkError(
          error.message || "Server tidak dapat dijangkau. Silakan coba lagi dalam beberapa saat."
        );
      }
    } finally {
      setIsProcessing(false);
    }
  };

  // Demo result preview from mockup (Qing Fen + Gan Cao + Dang Gui)
  const handleShowDemoResult = () => {
    setNetworkError(null);
    setResults({
      ingredients: [
        {
          matched_mandarin: "轻粉 · Qing Fen",
          indonesian_name: "Merkuri klorida (Calomel)",
          english_name: "Calomel / Mercurous Chloride",
          is_toxic: true,
          category: "toxic",
          description:
            "Mengandung merkuri klorida. Sangat tidak dianjurkan untuk ibu hamil, menyusui, dan penderita gangguan fungsi ginjal. Potensi akumulasi toksisitas logam berat.",
        },
        {
          matched_mandarin: "甘草 · Gan Cao",
          indonesian_name: "Akar Manis / Licorice",
          english_name: "Licorice Root",
          is_toxic: false,
          category: "safe",
          description: "Herbal harmonisator umum, meredakan batuk dan radang tenggorokan.",
        },
        {
          matched_mandarin: "当归 · Dang Gui",
          indonesian_name: "Dong Quai / Akar Angelica",
          english_name: "Angelica Sinensis",
          is_toxic: false,
          category: "safe",
          description: "Tonik sirkulasi darah tradisional yang aman dalam dosis standar.",
        },
      ],
      ocr_blocks: [
        { text: "轻粉" },
        { text: "甘草" },
        { text: "当归" },
      ],
      disclaimer:
        "MEDICAL DISCLAIMER: FitMate provides rule-based information only and does not substitute professional medical advice. Always consult a certified healthcare professional before consuming any TCM product.",
    });
  };

  const handleReset = () => {
    setImage(null);
    setResults(null);
    setNetworkError(null);
    setShowLiveCamera(false);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        handleImageReady(reader.result);
      }
    };
    reader.readAsDataURL(file);
  };

  // Drag & drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        handleImageReady(reader.result);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleBridgeComplete = (data: any) => {
    const sa = data.safety_analysis || {};
    const allIngredients = [
      ...(sa.toxic || []).map((i: any) => ({ ...i, category: "toxic", is_toxic: true })),
      ...(sa.contraindicated || []).map((i: any) => ({ ...i, category: "contraindicated", is_toxic: true })),
      ...(sa.safe || []).map((i: any) => ({ ...i, category: "safe", is_toxic: false })),
      ...(sa.unknown || []).map((i: any) => ({ ...i, category: "unknown", is_toxic: false })),
    ];
    setResults({
      ingredients: allIngredients,
      disclaimer: data.disclaimer || "",
      ocr_blocks: data.ocr_blocks || [],
    });
  };

  // Mobile Bridge Mode: When opened via QR Code scan on smartphone
  if (sessionParam) {
    return (
      <div className="w-full min-h-[85vh] flex flex-col items-center justify-center p-4">
        {bridgeUploaded && bridgeResults ? (
          <div className="w-full max-w-lg flex flex-col items-center animate-in zoom-in-95 duration-200">
            {/* Sync Success Header */}
            <div className="w-full bg-trust-tint border border-trust/40 rounded-[20px] p-5 mb-5 flex items-center justify-between gap-3 shadow-xs">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white text-trust-deep flex items-center justify-center shadow-xs">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-serif text-[15px] font-bold text-ink">
                    Tersinkron ke Layar Komputer!
                  </h3>
                  <p className="text-[12px] text-ink-soft">
                    Hasil analisis otomatis muncul di monitor desktop &amp; layar HP Anda.
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setBridgeUploaded(false);
                  setBridgeResults(null);
                }}
                className="px-3.5 py-2 bg-trust hover:bg-trust-deep text-white font-semibold text-[12px] rounded-[10px] shadow-xs transition cursor-pointer whitespace-nowrap"
              >
                Pindai Lagi
              </button>
            </div>

            {/* Render Full Results on Mobile as well */}
            <ResultsCard
              ingredients={bridgeResults.ingredients}
              ocrBlocks={bridgeResults.ocr_blocks}
              disclaimer={bridgeResults.disclaimer}
              onReset={() => {
                setBridgeUploaded(false);
                setBridgeResults(null);
              }}
            />
          </div>
        ) : bridgeUploading ? (
          <div className="bg-card border border-line rounded-[24px] p-10 max-w-sm w-full text-center shadow-xl">
            <ProcessingLoader />
            <p className="text-[13.5px] font-medium text-ink mt-5">
              Menganalisis label &amp; menghubungkan ke desktop...
            </p>
          </div>
        ) : (
          <div className="w-full max-w-md flex flex-col items-center">
            {/* Bridge Info Banner */}
            <div className="w-full mb-3 p-3 bg-trust-tint border border-trust/30 rounded-[14px] flex items-center gap-2.5 text-trust-deep text-[12px] font-medium">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-trust-deep flex-shrink-0">
                <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
                <line x1="12" y1="18" x2="12.01" y2="18" />
              </svg>
              <span>Jembatan Aktif: Foto akan otomatis disinkronkan ke komputer &amp; HP ini.</span>
            </div>

            <CameraViewfinder
              onCapture={async (base64) => {
                setBridgeUploading(true);
                try {
                  const resMsg = await fetch(base64);
                  const blob = await resMsg.blob();
                  const formData = new FormData();
                  formData.append("file", blob, "mobile_scan.jpg");

                  const apiUrl = getApiBaseUrl();
                  const uploadRes = await fetch(`${apiUrl}/api/v1/bridge/${sessionParam}/upload`, {
                    method: "POST",
                    body: formData,
                    signal: AbortSignal.timeout(45000),
                  });
                  if (!uploadRes.ok) {
                    throw new Error("Gagal mengunggah foto ke sesi desktop");
                  }
                  const uploadData = await uploadRes.json();
                  const sa = uploadData.safety_analysis || {};
                  const allIngredients = [
                    ...(sa.toxic || []).map((i: any) => ({ ...i, category: "toxic", is_toxic: true })),
                    ...(sa.contraindicated || []).map((i: any) => ({ ...i, category: "contraindicated", is_toxic: true })),
                    ...(sa.safe || []).map((i: any) => ({ ...i, category: "safe", is_toxic: false })),
                    ...(sa.unknown || []).map((i: any) => ({ ...i, category: "unknown", is_toxic: false })),
                  ];
                  setBridgeResults({
                    ingredients: allIngredients,
                    disclaimer: uploadData.disclaimer || "",
                    ocr_blocks: uploadData.ocr_blocks || [],
                  });
                  setBridgeUploaded(true);
                } catch (err: any) {
                  alert(err.message || "Gagal mengirim foto. Coba lagi.");
                } finally {
                  setBridgeUploading(false);
                }
              }}
              onReset={() => {
                window.location.href = "/";
              }}
            />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="w-full pb-16">
      {/* Hidden Global File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileInputChange}
      />

      {/* Main App Frame */}
      <div className="max-w-[1200px] mx-auto px-4 md:px-9 pt-6 md:pt-10">
        <div className="bg-paper rounded-[20px] border border-line shadow-[0_30px_60px_-30px_rgba(33,28,23,0.25)] overflow-hidden">
          
          {/* Active Result View State */}
          {results && (
            <div className="p-6 md:p-12 flex flex-col items-center">
              <ResultsCard
                ingredients={results.ingredients}
                ocrBlocks={results.ocr_blocks}
                disclaimer={results.disclaimer}
                onReset={handleReset}
              />
            </div>
          )}

          {/* Active Loader State */}
          {isProcessing && (
            <div className="p-12 md:p-20 flex flex-col items-center justify-center">
              <ProcessingLoader />
            </div>
          )}

          {/* Active Live Camera View State (Adaptive Widescreen Studio on Desktop, Portrait on Mobile) */}
          {showLiveCamera && !results && !isProcessing && (
            <div className="p-4 sm:p-6 md:p-8 flex flex-col items-center justify-center w-full">
              <CameraViewfinder onCapture={handleImageReady} onReset={handleReset} />
            </div>
          )}

          {/* Default Hero Presentation */}
          {!results && !isProcessing && !showLiveCamera && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-8 lg:gap-12 p-6 md:p-12 items-center">
                
                {/* Hero Copy (Left Column) */}
                <div className="flex flex-col items-start">
                  <div className="inline-flex items-center gap-2 bg-trust-tint text-trust-deep text-[11.5px] font-semibold px-3 py-1.5 rounded-full mb-4">
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.4"
                    >
                      <path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5z" />
                    </svg>
                    Rujukan BPOM &amp; SymMap
                  </div>

                  <h1 className="font-serif font-bold text-[32px] md:text-[38px] leading-[1.2] text-ink mb-4 max-w-[520px]">
                    Tahu isi obat TCM Anda sebelum meminumnya
                  </h1>

                  <p className="text-[14.5px] md:text-[15px] leading-[1.65] text-ink-soft mb-6 max-w-[480px]">
                    Pindai label komposisi obat tradisional China (TCM), terjemahkan aksara Hanzi, dan cocokkan kandungannya dengan daftar kompilasi resmi BPOM serta data toksisitas herbal.
                  </p>

                  {/* Primary Action Buttons: Standalone single-device workflow */}
                  <div className="flex flex-wrap items-center gap-3 mb-7 w-full sm:w-auto">
                    <button
                      onClick={() => setShowLiveCamera(true)}
                      className="px-5 py-2.5 bg-trust hover:bg-trust-deep text-white text-[13px] font-semibold rounded-[10px] shadow-sm transition flex items-center justify-center gap-2 active:scale-95 cursor-pointer flex-1 sm:flex-initial"
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                        <circle cx="12" cy="13" r="4" />
                      </svg>
                      Pindai via Kamera
                    </button>

                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="px-4 py-2.5 bg-paper-deep hover:bg-paper text-ink text-[13px] font-medium rounded-[10px] border border-line transition cursor-pointer flex items-center justify-center gap-1.5 flex-1 sm:flex-initial"
                    >
                      <svg
                        width="15"
                        height="15"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                      Pilih Foto Label
                    </button>

                    <button
                      onClick={handleShowDemoResult}
                      className="px-4 py-2.5 bg-transparent hover:bg-trust-tint text-trust-deep text-[13px] font-semibold rounded-[10px] border border-trust/50 transition active:scale-95 cursor-pointer w-full sm:w-auto"
                    >
                      Lihat Contoh Hasil
                    </button>
                  </div>

                  {/* Trust List */}
                  <div className="flex flex-col gap-2.5 text-[13px] text-ink-soft">
                    <div className="flex items-center gap-2.5">
                      <svg
                        width="15"
                        height="15"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.4"
                        strokeLinecap="round"
                        className="text-trust flex-shrink-0"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>Pencocokan aturan langsung dari monograf, bukan tebakan bebas</span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <svg
                        width="15"
                        height="15"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.4"
                        strokeLinecap="round"
                        className="text-trust flex-shrink-0"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>500 data bahan herbal dan zat berisiko dari BPOM serta SymMap</span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <svg
                        width="15"
                        height="15"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.4"
                        strokeLinecap="round"
                        className="text-trust flex-shrink-0"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>Tanya jawab seputar kandungan produk lewat bot WhatsApp</span>
                    </div>
                  </div>
                </div>

                {/* Hero Panel (Right Column: Standalone Dropzone + Optional QR Bridge) */}
                <div className="bg-card border border-line rounded-[20px] p-6 shadow-sm flex flex-col">
                  {/* Standalone Dropzone */}
                  <div
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className="border-[1.5px] border-dashed border-trust/40 bg-trust-tint/70 hover:bg-trust-tint rounded-[16px] p-8 text-center cursor-pointer transition-colors group"
                  >
                    <div className="w-[50px] h-[50px] rounded-full bg-white text-trust-deep flex items-center justify-center mx-auto mb-3 shadow-xs group-hover:scale-105 transition-transform">
                      <svg
                        width="22"
                        height="22"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                      >
                        <path d="M12 3v13" />
                        <path d="M7 8l5-5 5 5" />
                        <path d="M4 17v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
                      </svg>
                    </div>
                    <h4 className="text-[14.5px] font-semibold text-ink mb-1">
                      Seret foto label ke sini
                    </h4>
                    <p className="text-[12px] text-ink-soft mb-4">
                      atau klik untuk memilih file dari komputer/galeri (JPG, PNG, WebP)
                    </p>
                    <button
                      type="button"
                      className="w-full py-2.5 bg-trust hover:bg-trust-deep text-white text-[13px] font-semibold rounded-[10px] shadow-sm transition pointer-events-none"
                    >
                      Pilih Foto Label
                    </button>
                  </div>

                  {/* Optional QR Bridge (For Laptop Users wanting to use smartphone camera as scanner) */}
                  <div className="mt-4 pt-4 border-t border-line/60">
                    <button
                      type="button"
                      onClick={() => setShowQrBridge(!showQrBridge)}
                      className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-[12px] bg-paper-deep/60 hover:bg-paper-deep text-ink-soft hover:text-ink text-[12.5px] font-medium transition cursor-pointer border border-line/40"
                    >
                      <div className="flex items-center gap-2">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-trust flex-shrink-0">
                          <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
                          <line x1="12" y1="18" x2="12.01" y2="18" />
                        </svg>
                        <span>Ingin foto pakai kamera HP? (Jembatan QR)</span>
                      </div>
                      <span className="text-ink-faint text-[11px] font-semibold">
                        {showQrBridge ? "▲ Sembunyikan" : "▼ Buka QR"}
                      </span>
                    </button>

                    {showQrBridge && (
                      <div className="mt-3 animate-in fade-in slide-in-from-top-2 duration-200">
                        <QRCodeBridge onComplete={handleBridgeComplete} />
                      </div>
                    )}
                  </div>
                </div>
              </div>


              {/* Quick Feature Highlights */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4.5 px-6 md:px-12 pb-10 border-t border-line/60 pt-8 bg-paper-deep/30">
                <div className="bg-card border border-line rounded-[14px] p-5 shadow-xs">
                  <div className="w-[36px] h-[36px] rounded-[9px] bg-trust-tint text-trust-deep flex items-center justify-center mb-3">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <rect x="4" y="4" width="16" height="16" rx="2" />
                      <path d="M9 9h6v6H9z" />
                    </svg>
                  </div>
                  <h5 className="font-semibold text-[13.5px] text-ink mb-1.5">
                    Terjemahan Hanzi Instan
                  </h5>
                  <p className="text-[12px] leading-relaxed text-ink-soft">
                    Teks komposisi Mandarin diterjemahkan otomatis ke Bahasa Indonesia dan nama Latin ilmiah saat itu juga.
                  </p>
                </div>

                <div className="bg-card border border-line rounded-[14px] p-5 shadow-xs">
                  <div className="w-[36px] h-[36px] rounded-[9px] bg-danger-tint text-danger flex items-center justify-center mb-3">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M12 9v4M12 17h.01M10.3 3.9L2.5 17a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
                    </svg>
                  </div>
                  <h5 className="font-semibold text-[13.5px] text-ink mb-1.5">
                    Pencocokan Aturan Baku
                  </h5>
                  <p className="text-[12px] leading-relaxed text-ink-soft">
                    Dicocokkan ke 500 daftar bahan herbal dan zat berisiko dari literatur resmi tanpa halusinasi AI.
                  </p>
                </div>

                <div className="bg-card border border-line rounded-[14px] p-5 shadow-xs">
                  <div className="w-[36px] h-[36px] rounded-[9px] bg-trust-tint text-trust-deep flex items-center justify-center mb-3">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                  </div>
                  <h5 className="font-semibold text-[13.5px] text-ink mb-1.5">
                    Asisten Bot WhatsApp
                  </h5>
                  <p className="text-[12px] leading-relaxed text-ink-soft">
                    Tanyakan informasi bahan dan ringkasan umum secara otomatis melalui bot WhatsApp interaktif.
                  </p>
                </div>
              </div>
            </>
          )}

          {/* Network Error Toast */}
          {networkError && (
            <div className="m-6 p-4 rounded-[12px] bg-danger-tint border border-danger/30 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="text-danger flex-shrink-0"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <p className="text-[12.5px] text-ink">{networkError}</p>
              </div>
              <button
                onClick={handleReset}
                className="px-3 py-1 bg-danger text-white text-[11.5px] font-semibold rounded-md shadow-xs cursor-pointer"
              >
                Tutup
              </button>
            </div>
          )}
        </div>

        {/* Dedicated Section: CARA KERJA */}
        <section id="cara-kerja" className="mt-20 scroll-mt-24">
          <div className="text-center max-w-xl mx-auto mb-10">
            <span className="text-[12px] font-bold text-trust uppercase tracking-widest bg-trust-tint px-3 py-1 rounded-full">
              Langkah Sederhana
            </span>
            <h2 className="font-serif text-2xl md:text-3xl font-bold text-ink mt-3 mb-2">
              Cara Kerja FitMate TCM
            </h2>
            <p className="text-[13.5px] text-ink-soft leading-relaxed">
              3 tahapan cepat untuk memastikan ramuan herbal yang Anda konsumsi bebas dari zat berbahaya.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-card border border-line rounded-[18px] p-6 shadow-xs relative">
              <div className="text-3xl font-serif font-black text-trust/30 absolute top-5 right-6">
                01
              </div>
              <div className="w-11 h-11 rounded-[12px] bg-trust-tint text-trust-deep flex items-center justify-center mb-4">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                  <circle cx="12" cy="13" r="4" />
                </svg>
              </div>
              <h3 className="font-serif font-bold text-[16px] text-ink mb-2">
                1. Foto atau Unggah Label
              </h3>
              <p className="text-[13px] text-ink-soft leading-relaxed">
                Arahkan kamera ke label komposisi obat tradisional, atau unggah foto kemasan yang sudah Anda simpan di laptop atau ponsel.
              </p>
            </div>

            <div className="bg-card border border-line rounded-[18px] p-6 shadow-xs relative">
              <div className="text-3xl font-serif font-black text-trust/30 absolute top-5 right-6">
                02
              </div>
              <div className="w-11 h-11 rounded-[12px] bg-trust-tint text-trust-deep flex items-center justify-center mb-4">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
              </div>
              <h3 className="font-serif font-bold text-[16px] text-ink mb-2">
                2. Ekstraksi AI &amp; Aksara Hanzi
              </h3>
              <p className="text-[13px] text-ink-soft leading-relaxed">
                Vision AI membaca aksara Mandarin, mentranskripsikannya ke Pinyin, dan menerjemahkannya ke nama umum serta nama ilmiah Latin.
              </p>
            </div>

            <div className="bg-card border border-line rounded-[18px] p-6 shadow-xs relative">
              <div className="text-3xl font-serif font-black text-trust/30 absolute top-5 right-6">
                03
              </div>
              <div className="w-11 h-11 rounded-[12px] bg-danger-tint text-danger flex items-center justify-center mb-4">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
              </div>
              <h3 className="font-serif font-bold text-[16px] text-ink mb-2">
                3. Skrining Bahan &amp; Bot WhatsApp
              </h3>
              <p className="text-[13px] text-ink-soft leading-relaxed">
                Hasil dicocokkan ke 500 basis data herbal BPOM dan SymMap. Jika ada bahan berisiko seperti merkuri atau BKO, Anda dapat menanyakan rinciannya ke bot WhatsApp atau berkonsultasi ke dokter.
              </p>
            </div>
          </div>
        </section>

        {/* Dedicated Section: TENTANG */}
        <section id="tentang" className="mt-20 scroll-mt-24">
          <div className="text-center max-w-xl mx-auto mb-10">
            <span className="text-[12px] font-bold text-heritage uppercase tracking-widest bg-heritage/10 text-heritage px-3 py-1 rounded-full">
              Komitmen Keamanan
            </span>
            <h2 className="font-serif text-2xl md:text-3xl font-bold text-ink mt-3 mb-2">
              Tentang FitMate TCM
            </h2>
            <p className="text-[13.5px] text-ink-soft leading-relaxed">
              Misi kami adalah melindungi kesehatan masyarakat Indonesia dari peredaran obat tradisional yang tercemar atau berisiko tinggi.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-card border border-line rounded-[18px] p-6 shadow-xs">
              <h4 className="font-serif font-bold text-[16px] text-ink mb-2">
                Standar Regulasi BPOM &amp; FHI
              </h4>
              <p className="text-[13px] text-ink-soft leading-relaxed">
                Basis data kami mengacu pada monograf Farmakope Herbal Indonesia, pedoman keamanan Badan POM RI mengenai Bahan Kimia Obat (BKO), dan literatur toksikologi SymMap.
              </p>
            </div>

            <div className="bg-card border border-line rounded-[18px] p-6 shadow-xs">
              <h4 className="font-serif font-bold text-[16px] text-ink mb-2">
                Prinsip Zero-Hallucination
              </h4>
              <p className="text-[13px] text-ink-soft leading-relaxed">
                FitMate tidak menyerahkan penentuan aman atau bahaya pada tebakan model AI bebas. Seluruh status bahan dipetakan langsung menggunakan aturan deterministik dari pustaka data resmi.
              </p>
            </div>

            <div className="bg-card border border-line rounded-[18px] p-6 shadow-xs">
              <h4 className="font-serif font-bold text-[16px] text-ink mb-2">
                Transparansi Informasi Herbal
              </h4>
              <p className="text-[13px] text-ink-soft leading-relaxed">
                Membantu masyarakat awam memahami komposisi aksara Mandarin pada kemasan obat tradisional secara transparan, mudah dibaca, dan berbasis kompilasi data publik.
              </p>
            </div>
          </div>

          {/* Medical Disclaimer Banner */}
          <div className="mt-8 bg-paper-deep border border-line rounded-[16px] p-6 flex flex-col md:flex-row items-start gap-4">
            <div className="w-10 h-10 rounded-full bg-line flex items-center justify-center flex-shrink-0 text-ink">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <line x1="12" y1="8" x2="12" y2="14" />
                <line x1="9" y1="11" x2="15" y2="11" />
              </svg>
            </div>
            <div>
              <h5 className="font-bold text-[13px] text-ink uppercase tracking-wider mb-1">
                Pernyataan Penafian Medis Resmi (Medical Disclaimer)
              </h5>
              <p className="text-[12.5px] text-ink-soft leading-relaxed">
                FitMate TCM adalah perangkat lunak skrining edukatif dan pendukung keputusan awal. Hasil analisis bukan merupakan diagnosis medis, resep, atau pengganti konsultasi langsung dengan dokter spesialis atau apoteker profesional. Jangan menghentikan atau mengubah pengobatan medis Anda tanpa persetujuan dokter.
              </p>
            </div>
          </div>
        </section>

        {/* Simple Footer with Prototype Notice */}
        <footer className="mt-20 pt-8 border-t border-line text-center text-[12px] text-ink-faint flex flex-col items-center gap-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-paper-deep text-ink-soft text-[11px] font-semibold border border-line">
            <span className="w-1.5 h-1.5 rounded-full bg-amber" />
            <span>Versi Prototipe Riset (Bukan Pelayanan Medis Resmi)</span>
          </div>
          <p className="max-w-2xl leading-relaxed">
            © 2026 FitMate TCM. Proyek ini merupakan prototipe aplikasi untuk edukasi dan skrining awal mandiri. Seluruh basis data dikompilasi dari publikasi publik BPOM dan SymMap, serta belum divalidasi oleh praktisi klinis atau apoteker independen.
          </p>
        </footer>
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="w-full min-h-[60vh] flex items-center justify-center p-8 text-ink-soft text-sm">
          <svg className="animate-spin inline-block h-5 w-5 mr-2 text-trust" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Memuat FitMate TCM...
        </div>
      }
    >
      <HomeContent />
    </Suspense>
  );
}

