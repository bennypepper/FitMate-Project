"use client";

import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/adminApi";
import Link from "next/link";

const navItems = [
  {
    href: "/admin",
    label: "Analitik Scan",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 3v18h18" />
        <path d="M7 15l4-4 3 3 5-6" />
      </svg>
    ),
  },
  {
    href: "/admin/ingredients",
    label: "Basis Pengetahuan",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </svg>
    ),
  },
  {
    href: "/admin/upload",
    label: "Unggah Data",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 3v13" />
        <path d="M7 8l5-5 5 5" />
        <path d="M4 17v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
      </svg>
    ),
  },
];

export default function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    clearToken();
    router.replace("/admin/login");
  };

  const isActive = (href: string) =>
    href === "/admin" ? pathname === "/admin" : pathname.startsWith(href);

  return (
    <>
      {/* ── Desktop Sidebar ── */}
      <aside className="hidden lg:flex flex-col w-[236px] bg-card border-r border-line p-5 h-screen sticky top-0">
        {/* Brandmark */}
        <div className="px-2 pb-5 border-b border-line mb-5">
          <div className="font-serif italic font-bold text-heritage text-[17px]">
            FitMate TCM
          </div>
          <div className="text-[11px] text-ink-faint mt-0.5">Admin Console</div>
        </div>

        {/* Navigation Links */}
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-[10px] text-[13.5px] transition-colors border-l-[3px] ${
                  active
                    ? "bg-trust-tint text-trust-deep font-semibold border-trust"
                    : "text-ink-soft hover:text-ink hover:bg-paper font-medium border-transparent"
                }`}
              >
                <span className="flex-shrink-0">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Admin User Profile */}
        <div className="pt-3 border-t border-line mt-2">
          <div className="flex items-center gap-2.5 px-2 py-2">
            <div className="w-[34px] h-[34px] rounded-full bg-amber-tint text-amber flex items-center justify-center font-bold text-[13px] flex-shrink-0">
              A
            </div>
            <div className="flex flex-col min-w-0">
              <strong className="text-[12.5px] text-ink leading-tight truncate">
                Administrator
              </strong>
              <span className="text-[10.5px] text-ink-faint leading-tight">
                FitMate Admin
              </span>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full text-left text-[12px] font-semibold text-danger hover:text-danger-deep px-2 py-1.5 transition-colors cursor-pointer"
          >
            Keluar dengan aman
          </button>
        </div>
      </aside>

      {/* ── Mobile Admin Header & Navigation ── */}
      <div className="lg:hidden w-full bg-card border-b border-line px-4 py-3 flex items-center justify-between sticky top-0 z-30">
        <div>
          <span className="font-serif italic font-bold text-heritage text-[16px]">
            FitMate TCM
          </span>
          <span className="text-[10px] text-ink-faint ml-2">Console</span>
        </div>
        <div className="flex items-center gap-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`p-2 rounded-lg text-xs ${
                isActive(item.href)
                  ? "bg-trust-tint text-trust-deep font-bold"
                  : "text-ink-soft"
              }`}
              title={item.label}
            >
              {item.icon}
            </Link>
          ))}
          <button
            onClick={handleLogout}
            className="text-xs text-danger font-semibold ml-2 p-1"
            title="Keluar"
          >
            Keluar
          </button>
        </div>
      </div>
    </>
  );
}
