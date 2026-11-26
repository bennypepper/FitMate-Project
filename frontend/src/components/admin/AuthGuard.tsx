"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getToken, isTokenExpired, clearToken } from "@/lib/adminApi";

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * AuthGuard: wraps all /admin/* routes except /admin/login.
 * Checks localStorage for a valid (non-expired) JWT on client mount.
 * Server renders a loading state to avoid hydration mismatch.
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const isLoginPage = pathname === "/admin/login";
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (isLoginPage) {
      return;
    }

    const token = getToken();
    if (!token || isTokenExpired(token)) {
      clearToken();
      queueMicrotask(() => {
        setAuthorized(false);
      });
      router.replace("/admin/login");
      return;
    }

    queueMicrotask(() => {
      setAuthorized(true);
    });
  }, [isLoginPage, pathname, router]);

  if (!authorized && !isLoginPage) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <p className="font-sans text-ink-soft text-sm">
          Memverifikasi sesi...
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
