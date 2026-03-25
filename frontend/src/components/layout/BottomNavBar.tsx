import Link from "next/link";

export default function BottomNavBar() {
  return (
    <nav className="fixed bottom-0 left-0 w-full flex justify-around items-center px-4 pb-6 pt-3 bg-white/90 backdrop-blur-xl z-50 rounded-t-[14px] shadow-[0_-8px_24px_rgba(0,0,0,0.05)] border-t border-light/20">
      <Link href="/">
        <button className="flex flex-col items-center justify-center bg-primary text-white rounded-[10px] px-4 py-1.5 transition-transform active:scale-95">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
            photo_camera
          </span>
          <span className="text-[10px] font-bold uppercase tracking-wider mt-1">Pemindai</span>
        </button>
      </Link>
      <button className="flex flex-col items-center justify-center text-on-surface-variant px-4 py-1.5 hover:text-primary">
        <span className="material-symbols-outlined">history</span>
        <span className="text-[10px] font-bold uppercase tracking-wider mt-1">Riwayat</span>
      </button>
      <button className="flex flex-col items-center justify-center text-on-surface-variant px-4 py-1.5 hover:text-primary">
        <span className="material-symbols-outlined">chat</span>
        <span className="text-[10px] font-bold uppercase tracking-wider mt-1">Konsultasi</span>
      </button>
      <Link href="/admin">
        <button className="flex flex-col items-center justify-center text-on-surface-variant px-4 py-1.5 hover:text-primary">
          <span className="material-symbols-outlined">dashboard</span>
          <span className="text-[10px] font-bold uppercase tracking-wider mt-1">Admin</span>
        </button>
      </Link>
    </nav>
  );
}
