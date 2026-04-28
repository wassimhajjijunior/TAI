import type { ReactNode } from "react";
import "@/app/globals.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";
import Link from "next/link";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});


type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className={cn("font-sans", geist.variable)}>
      <body className="min-h-screen bg-background">
        <header className="border-b bg-card/80 backdrop-blur">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3">
            <h1 className="text-xl font-semibold tracking-tight">P2M-TAI</h1>
            <nav className="flex items-center gap-4 text-sm font-medium">
              <Link href="/dashboard" className="text-muted-foreground hover:text-foreground">
                Dashboard
              </Link>
              <Link href="/dashboard/tenders" className="text-muted-foreground hover:text-foreground">
                Tenders
              </Link>
              <Link href="/dashboard/activity" className="text-muted-foreground hover:text-foreground">
                Activity
              </Link>
              <Link href="/dashboard/company/profile" className="text-muted-foreground hover:text-foreground">
                Company
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
