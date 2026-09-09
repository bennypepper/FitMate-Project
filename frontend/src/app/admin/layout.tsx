"use client";

import { usePathname } from "next/navigation";
import AuthGuard from "@/components/admin/AuthGuard";
import AdminSidebar from "@/components/admin/AdminSidebar";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/admin/login";

  if (isLoginPage) {
    return (
      <div className="min-h-screen bg-paper-deep flex items-center justify-center p-4">
        {children}
      </div>
    );
  }

  return (
    <AuthGuard>
      <div className="flex flex-col lg:flex-row min-h-screen bg-paper">
        <AdminSidebar />
        <main className="flex-1 overflow-y-auto pb-16 lg:pb-0 bg-paper">
          {children}
        </main>
      </div>
    </AuthGuard>
  );
}
