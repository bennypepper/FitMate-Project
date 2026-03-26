import Link from "next/link";

export default function TopAppBar() {
  return (
    <header className="bg-white sticky top-0 z-50 border-b border-light/20">
      <div className="flex justify-between items-center w-full px-6 py-4 max-w-7xl mx-auto">
        <div className="text-2xl font-headline italic text-primary">FitMate TCM</div>
        <div className="flex items-center gap-4">
          <Link href="/admin">
            <button className="material-symbols-outlined text-primary p-2 rounded-full hover:bg-light/10 transition-colors">
              account_circle
            </button>
          </Link>
        </div>
      </div>
    </header>
  );
}
