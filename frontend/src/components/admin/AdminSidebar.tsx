"use client";

import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/adminApi";

const navItems = [
  { href: "/admin", label: "Dasbor", icon: "dashboard" },
  { href: "/admin/ingredients", label: "Daftar Bahan", icon: "menu_book" },
  { href: "/admin/upload", label: "Unggah Data", icon: "upload_file" },
];

/**
 * AdminSidebar — matches the stitch_pkm_ki_fitme_v1/dashboard_admin/code.html sidebar layout.
 * Desktop: fixed left sidebar (w-72).
 * Mobile: bottom nav bar with glassmorphism.
 */
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
      <aside className="hidden lg:flex flex-col h-screen sticky top-0 w-72 bg-surface-container-lowest border-r border-surface-container-low">
        {/* Brand */}
        <div className="px-8 pt-10 pb-8">
          <h1 className="font-serif text-xl font-bold text-primary italic">
            Admin Console
          </h1>
          <p className="font-sans text-[10px] uppercase tracking-widest text-on-surface-variant opacity-60 mt-1">
            FitMate TCM Systems
          </p>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-4 space-y-1">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className={`flex items-center gap-4 px-4 py-3 rounded-r-full transition-all ${
                isActive(item.href)
                  ? "bg-surface-container-low text-primary font-bold"
                  : "text-on-surface-variant hover:pl-6 hover:bg-surface-container-low"
              }`}
            >
              <span className="material-symbols-outlined text-xl">{item.icon}</span>
              <span className="font-sans text-sm font-medium">{item.label}</span>
            </a>
          ))}
        </nav>

        {/* User + Logout */}
        <div className="px-8 py-8 border-t border-surface-container-low">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-primary text-base">
                admin_panel_settings
              </span>
            </div>
            <div>
              <p className="font-sans text-sm font-bold text-on-surface">
                Administrator
              </p>
              <p className="font-sans text-[10px] uppercase tracking-tight text-on-surface-variant">
                FitMate Admin
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full py-2 px-4 rounded-xl border border-primary text-primary font-sans text-sm font-semibold hover:bg-primary hover:text-white transition-all active:scale-95"
          >
            Secure Logout
          </button>
        </div>
      </aside>

      {/* ── Mobile Bottom Nav ── */}
      <nav className="lg:hidden fixed bottom-0 left-0 w-full flex justify-around items-center px-4 pb-6 pt-3 bg-surface-container-lowest/80 backdrop-blur-xl z-50 rounded-t-3xl border-t border-surface-container-low shadow-ambient">
        {navItems.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center justify-center px-4 py-1 rounded-2xl transition-transform active:scale-90 ${
              isActive(item.href)
                ? "bg-surface-container-low text-primary"
                : "text-on-surface-variant"
            }`}
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span className="text-[10px] font-sans font-medium uppercase tracking-wider mt-0.5">
              {item.label.split(" ")[0]}
            </span>
          </a>
        ))}
      </nav>
    </>
  );
}
