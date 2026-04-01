"use client";

import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/adminApi";
import Link from "next/link";

const navItems = [
  { href: "/admin", label: "Analitik Scan", icon: "analytics" },
  { href: "/admin/ingredients", label: "Basis Pengetahuan", icon: "menu_book" },
  { href: "/admin/upload", label: "Unggah Data", icon: "upload_file" },
];

export default function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    clearToken();
    router.replace("/admin/login");
  };

  const isActive = (href: string) =>
    href === "/admin"
      ? pathname === "/admin"
      : pathname.startsWith(href);

  return (
    <>
      {/* ── Desktop Sidebar ── */}
      <aside className="hidden lg:flex flex-col h-screen max-h-[100dvh] sticky top-0 w-72 bg-surface border-r border-light/50">
        {/* Brand */}
        <div className="p-6 pb-2">
          <h1 className="font-headline text-xl text-primary font-bold">Admin Console</h1>
          <p className="font-body text-xs text-on-surface-variant opacity-70 mt-1">
            FitMate TCM Systems
          </p>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 mt-4 overflow-y-auto">
          <ul className="space-y-1">
            {navItems.map((item) => (
              <li key={item.href} className="px-4">
                <Link
                  href={item.href}
                  className={`flex items-center gap-4 px-4 py-3 rounded-r-full transition-all ${
                    isActive(item.href)
                      ? "bg-light/50 text-primary font-bold"
                      : "text-on-surface-variant hover:pl-6 hover:bg-light/30"
                  }`}
                >
                  <span className="material-symbols-outlined text-xl">{item.icon}</span>
                  <span className="font-body font-medium">{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* User + Logout */}
        <div className="p-6 border-t border-light/50 mt-auto">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-light flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-primary text-base">
                admin_panel_settings
              </span>
            </div>
            <div>
              <p className="font-body text-sm font-bold text-dark">
                Administrator
              </p>
              <p className="font-body text-[10px] uppercase tracking-tighter text-on-surface-variant">
                FitMate Admin
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full py-2 px-4 rounded-xl border border-primary text-primary font-body text-sm font-semibold hover:bg-primary hover:text-white transition-all active:scale-95"
          >
            Secure Logout
          </button>
        </div>
      </aside>

      {/* ── Mobile Bottom Nav ── */}
      <nav className="lg:hidden fixed bottom-0 left-0 w-full flex justify-around items-center px-4 pb-6 pt-3 bg-surface/90 backdrop-blur-xl z-50 rounded-t-3xl border-t border-light/50 shadow-ambient">
        {/* We keep standard app nav behavior for mobile here, or just dashboard links */}
        <Link
          href="/"
          className="flex flex-col items-center justify-center text-on-surface-variant px-4 py-1 hover:text-primary transition-colors"
        >
          <span className="material-symbols-outlined">photo_camera</span>
          <span className="text-[11px] font-body font-medium uppercase tracking-wider mt-1">
            Scanner
          </span>
        </Link>
        <Link
          href="/admin"
          className={`flex flex-col items-center justify-center px-4 py-1 rounded-xl transition-transform active:scale-90 ${
            pathname === "/admin" ? "bg-light/50 text-primary" : "text-on-surface-variant"
          }`}
        >
          <span className="material-symbols-outlined">dashboard</span>
          <span className="text-[11px] font-body font-medium uppercase tracking-wider mt-1">
            Admin
          </span>
        </Link>
        <button
          onClick={handleLogout}
          className="flex flex-col items-center justify-center text-on-surface-variant px-4 py-1 hover:text-primary transition-colors"
        >
          <span className="material-symbols-outlined">logout</span>
          <span className="text-[11px] font-body font-medium uppercase tracking-wider mt-1">
            Keluar
          </span>
        </button>
      </nav>
    </>
  );
}

