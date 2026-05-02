"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function TopBar() {
  const pathname = usePathname();
  
  const showApproveButton = pathname.includes("/tenders/") && 
    !pathname.includes("/new") && 
    !pathname.includes("/tenders?");

  return (
    <header className="w-full sticky top-0 z-50 bg-[#FAF8FF] border-b border-[#434655]/15 flex justify-between items-center h-16 px-8">
      <div className="flex items-center gap-8">
        <div className="text-xl font-bold tracking-tighter text-[#131B2E] font-headline">
          Sovereign Bid Assistant
        </div>
        <nav className="hidden md:flex gap-6">
          <Link
            href="/dashboard"
            className="text-[#434655] font-semibold text-sm px-2 py-1 hover:bg-[#F2F3FF] transition-colors"
          >
            Home
          </Link>
          <Link
            href="/dashboard/activity"
            className={cn(
              "font-semibold text-sm px-2 py-1 transition-colors",
              pathname === "/dashboard/activity"
                ? "text-[#004AC6] font-bold border-b-2 border-[#004AC6]"
                : "text-[#434655] hover:bg-[#F2F3FF]"
            )}
          >
            System Status
          </Link>
          <Link
            href="/dashboard/activity"
            className="text-[#434655] font-semibold text-sm px-2 py-1 hover:bg-[#F2F3FF] transition-colors"
          >
            Audit Logs
          </Link>
        </nav>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex gap-2 mr-4">
          <button className="p-2 text-[#434655] hover:bg-[#F2F3FF] rounded-full transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>
          <button className="p-2 text-[#434655] hover:bg-[#F2F3FF] rounded-full transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <button className="p-2 text-[#434655] hover:bg-[#F2F3FF] rounded-full transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </button>
        </div>
        {showApproveButton && (
          <button className="bg-gradient-to-r from-[#004AC6] to-[#2563EB] text-white px-5 py-2 rounded-xl font-bold text-sm shadow-md transition-transform active:scale-95">
            Approve Tender
          </button>
        )}
      </div>
    </header>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
