import Link from "next/link";

export default function TopAppBar() {
  return (
    <header className="bg-white sticky top-0 z-50 border-b border-light/20">
      <div className="flex justify-between items-center w-full px-6 py-4 max-w-7xl mx-auto">
        <div className="text-2xl font-headline italic text-primary">FitMate TCM</div>
        <div className="hidden md:flex gap-8 items-center">
          <Link href="/" className="text-primary font-bold border-b-2 border-accent transition-colors px-2 py-1">
            Pemindai
          </Link>
          <a className="text-on-surface-variant hover:text-primary transition-colors px-2 py-1" href="#">
            Riwayat
          </a>
          <a className="text-on-surface-variant hover:text-primary transition-colors px-2 py-1" href="#">
            Konsultasi
          </a>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/admin">
            <button className="material-symbols-outlined text-primary p-2 rounded-full hover:bg-light/10 transition-colors">
              account_circle
            </button>
          </Link>
          <button className="material-symbols-outlined text-primary p-2 rounded-full hover:bg-light/10 transition-colors">
            menu
          </button>
        </div>
      </div>
    </header>
  );
}
