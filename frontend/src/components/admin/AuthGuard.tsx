"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getToken, isTokenExpired, clearToken } from "@/lib/adminApi";

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * AuthGuard — wraps all /admin/* routes except /admin/login.
 * Checks localStorage for a valid (non-expired) JWT on client mount.
 * Server renders a loading state to avoid hydration mismatch.
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  const [authorized, setAuthorized] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (pathname === "/admin/login") {
      setAuthorized(true);
      return;
    }

    const token = getToken();
    if (!token || isTokenExpired(token)) {
      clearToken();
      router.replace("/admin/login");
      return;
    }

    setAuthorized(true);
  }, [pathname, router]);

  if (!authorized) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <p className="font-sans text-on-surface-variant text-sm">
          Memverifikasi sesi...
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
