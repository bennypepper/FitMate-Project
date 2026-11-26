import Link from "next/link";

export default function NotFoundPage() {
  return (
    <div className="flex-1 flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md bg-card border border-line rounded-[20px] p-8 text-center shadow-sm">
        <span className="inline-block px-3 py-1 rounded-full bg-paper-deep border border-line text-[11.5px] font-bold tracking-wider text-ink-soft uppercase mb-4">
          404
        </span>
        <h1 className="font-serif text-2xl font-bold text-ink mb-2">
          Halaman Tidak Ditemukan
        </h1>
        <p className="text-[13.5px] text-ink-soft leading-relaxed mb-6">
          Tautan yang Anda buka tidak tersedia atau telah dipindahkan. Kembali
          ke halaman utama untuk memindai label TCM.
        </p>
        <Link
          href="/"
          className="inline-flex items-center justify-center px-5 py-2.5 rounded-[10px] bg-trust hover:bg-trust-deep text-white text-[13px] font-semibold transition"
        >
          Kembali ke Beranda
        </Link>
      </div>
    </div>
  );
}
