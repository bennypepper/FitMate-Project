import type { Metadata } from "next";
import AuthGuard from "@/components/admin/AuthGuard";
import AdminSidebar from "@/components/admin/AdminSidebar";

export const metadata: Metadata = {
  title: "FitMate Admin Console",
  description: "Admin dashboard untuk manajemen basis pengetahuan TCM FitMate",
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {/* Material Symbols Outlined for icon font */}
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap"
      />
      <AuthGuard>
        <div className="flex min-h-screen bg-surface-container-lowest overflow-hidden">
          <AdminSidebar />
          <main className="flex-1 overflow-y-auto pb-20 lg:pb-0">
            {children}
          </main>
        </div>
      </AuthGuard>
    </>
  );
}
