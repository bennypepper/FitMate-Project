"use client";

import { useState, useRef } from "react";
import CameraViewfinder from "@/components/scanner/CameraViewfinder";
import ProcessingLoader from "@/components/scanner/ProcessingLoader";
import ResultsCard from "@/components/results/ResultsCard";

export default function HomePage() {
  const [image, setImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<any | null>(null);
  const [networkError, setNetworkError] = useState<string | null>(null);
  const [showLiveCamera, setShowLiveCamera] = useState(false);
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

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://benedictpepper-fitmate-api.hf.space";
      const response = await fetch(`${apiUrl}/api/v1/analyze/`, {
        method: "POST",
        body: formData,
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

      {/* Caption Banner (from Mockup) */}
      <section className="hidden md:block max-w-[1200px] mx-auto px-6 md:px-9 pt-10 pb-4">
        <div className="text-[12px] font-semibold text-trust-deep tracking-wider mb-1 uppercase">
          Desktop — Sisi Konsumen
        </div>
        <h2 className="font-serif text-[22px] font-bold text-ink mb-1.5">
          Bukan versi mobile yang direntangkan
        </h2>
        <p className="text-[13.5px] leading-relaxed text-ink-soft max-w-[660px]">
          Di desktop, kamera belakang HP tidak tersedia dan pengguna jarang memegang label obat di
          depan webcam. Jadi desktop dirancang untuk dua kebutuhan nyata: unggah foto yang sudah ada,
          atau lanjutkan pemindaian langsung di HP lewat QR — bukan meniru layar kamera mobile di layar besar.
        </p>
      </section>

      {/* Main App Frame */}
      <div className="max-w-[1200px] mx-auto px-4 md:px-9">
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

          {/* Active Live Camera View State (if triggered on desktop/mobile) */}
          {showLiveCamera && !results && !isProcessing && (
            <div className="p-6 md:p-10 flex flex-col items-center justify-center">
              <CameraViewfinder onCapture={handleImageReady} onReset={handleReset} />
            </div>
          )}

          {/* Default Hero Presentation (Mockup Section 1) */}
          {!results && !isProcessing && !showLiveCamera && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-10 lg:gap-14 p-6 md:p-12 items-center">
                
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
                    Diverifikasi apoteker terdaftar
                  </div>

                  <h1 className="font-serif font-bold text-[34px] md:text-[38px] leading-[1.2] text-ink mb-4 max-w-[520px]">
                    Tahu isi obat TCM Anda sebelum meminumnya
                  </h1>

                  <p className="text-[14.5px] md:text-[15px] leading-[1.65] text-ink-soft mb-6 max-w-[480px]">
                    FitMate memindai label komposisi, menerjemahkan aksara Hanzi, dan mencocokkannya
                    dengan basis data toksisitas — supaya bahan berbahaya seperti merkuri atau arsenik
                    tidak lolos dari perhatian.
                  </p>

                  <div className="flex flex-wrap items-center gap-3 mb-7">
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="px-5 py-2.5 bg-trust hover:bg-trust-deep text-white text-[13px] font-semibold rounded-[10px] shadow-sm transition flex items-center gap-2 active:scale-95 cursor-pointer"
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <rect x="3" y="6" width="18" height="14" rx="2" />
                        <path d="M8 6l2-3h4l2 3" />
                        <circle cx="12" cy="13" r="3.5" />
                      </svg>
                      Unggah foto label
                    </button>

                    <button
                      onClick={handleShowDemoResult}
                      className="px-5 py-2.5 bg-transparent hover:bg-trust-tint text-trust-deep text-[13px] font-semibold rounded-[10px] border border-trust transition active:scale-95 cursor-pointer"
                    >
                      Lihat contoh hasil
                    </button>

                    <button
                      onClick={() => setShowLiveCamera(true)}
                      className="px-4 py-2.5 bg-paper-deep hover:bg-paper text-ink text-[13px] font-medium rounded-[10px] border border-line transition cursor-pointer flex items-center gap-1.5"
                    >
                      <svg
                        width="15"
                        height="15"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                        <circle cx="12" cy="13" r="4" />
                      </svg>
                      Buka Kamera HP
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
                      <span>Panduan rule-based, bukan tebakan AI</span>
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
                      <span>Bahan dicocokkan ke basis data toksisitas tervalidasi</span>
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
                      <span>Lanjutkan konsultasi langsung via WhatsApp</span>
                    </div>
                  </div>
                </div>

                {/* Hero Panel (Right Column: Dropzone & QR Bridge) */}
                <div className="bg-card border border-line rounded-[20px] p-6 shadow-sm flex flex-col">
                  {/* Dropzone */}
                  <div
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className="border-[1.5px] border-dashed border-trust/40 bg-trust-tint hover:bg-trust-tint/80 rounded-[14px] p-8 text-center cursor-pointer transition-colors group"
                  >
                    <div className="w-[46px] h-[46px] rounded-full bg-white text-trust-deep flex items-center justify-center mx-auto mb-3 shadow-xs group-hover:scale-105 transition-transform">
                      <svg
                        width="20"
                        height="20"
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
                    <h4 className="text-[14px] font-semibold text-ink mb-1">
                      Seret foto label ke sini
                    </h4>
                    <p className="text-[12px] text-ink-soft mb-4">
                      atau klik untuk memilih file — JPG, PNG, maks 10MB
                    </p>
                    <button
                      type="button"
                      className="w-full py-2.5 bg-trust hover:bg-trust-deep text-white text-[13px] font-semibold rounded-[10px] shadow-sm transition"
                    >
                      Pilih File
                    </button>
                  </div>

                  {/* Divider */}
                  <div className="flex items-center gap-3 my-5 text-[11px] font-bold text-ink-faint tracking-wider">
                    <div className="flex-1 h-[1px] bg-line" />
                    <span>ATAU LANJUTKAN DI HP</span>
                    <div className="flex-1 h-[1px] bg-line" />
                  </div>

                  {/* QR Bridge */}
                  <div className="flex items-center gap-4 bg-paper/60 p-3 rounded-[12px] border border-line/60">
                    <div className="w-[76px] h-[76px] bg-ink rounded-[10px] flex-shrink-0 relative overflow-hidden flex items-center justify-center p-1.5 shadow-xs">
                      {/* Styled Vector QR Representation */}
                      <svg viewBox="0 0 33 33" className="w-full h-full text-white fill-current">
                        <rect x="0" y="0" width="10" height="10" />
                        <rect x="2" y="2" width="6" height="6" fill="#211C17" />
                        <rect x="4" y="4" width="2" height="2" />
                        
                        <rect x="23" y="0" width="10" height="10" />
                        <rect x="25" y="2" width="6" height="6" fill="#211C17" />
                        <rect x="27" y="4" width="2" height="2" />

                        <rect x="0" y="23" width="10" height="10" />
                        <rect x="2" y="25" width="6" height="6" fill="#211C17" />
                        <rect x="4" y="27" width="2" height="2" />

                        <rect x="13" y="2" width="3" height="3" />
                        <rect x="17" y="5" width="3" height="3" />
                        <rect x="13" y="13" width="7" height="7" />
                        <rect x="15" y="15" width="3" height="3" fill="#211C17" />
                        <rect x="2" y="13" width="3" height="3" />
                        <rect x="7" y="17" width="3" height="3" />
                        <rect x="23" y="13" width="4" height="4" />
                        <rect x="28" y="19" width="3" height="3" />
                        <rect x="13" y="24" width="4" height="4" />
                        <rect x="19" y="27" width="3" height="3" />
                        <rect x="25" y="25" width="5" height="5" />
                      </svg>
                    </div>

                    <div className="flex-1">
                      <h5 className="font-semibold text-[13px] text-ink mb-1">
                        Pindai kode ini dengan kamera HP
                      </h5>
                      <p className="text-[11.5px] leading-relaxed text-ink-soft">
                        Sesi otomatis tersambung — buka langsung di browser HP tanpa install aplikasi.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Feature Cards Row */}
              <div id="cara-kerja" className="grid grid-cols-1 md:grid-cols-3 gap-4.5 px-6 md:px-12 pb-12">
                <div className="bg-card border border-line rounded-[14px] p-5 shadow-xs">
                  <div className="w-[36px] h-[36px] rounded-[9px] bg-amber-tint text-amber flex items-center justify-center mb-3">
                    <svg
                      width="17"
                      height="17"
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
                    Terjemahan Hanzi instan
                  </h5>
                  <p className="text-[12px] leading-relaxed text-ink-soft">
                    Teks komposisi diterjemahkan otomatis ke Bahasa Indonesia saat itu juga menggunakan
                    vision multimodal AI.
                  </p>
                </div>

                <div className="bg-card border border-line rounded-[14px] p-5 shadow-xs">
                  <div className="w-[36px] h-[36px] rounded-[9px] bg-amber-tint text-amber flex items-center justify-center mb-3">
                    <svg
                      width="17"
                      height="17"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M12 9v4M12 17h.01M10.3 3.9L2.5 17a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
                    </svg>
                  </div>
                  <h5 className="font-semibold text-[13.5px] text-ink mb-1.5">
                    Deteksi bahan berisiko
                  </h5>
                  <p className="text-[12px] leading-relaxed text-ink-soft">
                    Dicocokkan ke basis data toksisitas yang dikelola apoteker terdaftar dengan aturan ketat zero-hallucination.
                  </p>
                </div>

                <div id="tentang" className="bg-card border border-line rounded-[14px] p-5 shadow-xs">
                  <div className="w-[36px] h-[36px] rounded-[9px] bg-amber-tint text-amber flex items-center justify-center mb-3">
                    <svg
                      width="17"
                      height="17"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                  </div>
                  <h5 className="font-semibold text-[13.5px] text-ink mb-1.5">
                    Konsultasi lanjutan
                  </h5>
                  <p className="text-[12px] leading-relaxed text-ink-soft">
                    Temuan berisiko langsung terhubung ke konsultan WhatsApp berbasis aturan untuk bantuan klinis lebih lanjut.
                  </p>
                </div>
              </div>
            </>
          )}

          {/* Network Error Toast / Banner */}
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
                className="px-3 py-1 bg-danger text-white text-[11.5px] font-semibold rounded-md shadow-xs"
              >
                Tutup
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
