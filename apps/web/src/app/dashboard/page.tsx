"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { SignOutButton } from "@/components/auth/sign-out-button";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, loading, user } = useAuth();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return <div>Checking session...</div>;
  }

  if (!isAuthenticated) {
    return <div>Redirecting to login...</div>;
  }

  return (
    <section>
      <h2>Dashboard</h2>
      <p>Connected as {user?.email}</p>
      <SignOutButton />
    </section>
  );
}
