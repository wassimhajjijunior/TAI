"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "dashboard" },
  { href: "/dashboard/tenders", label: "Tender Library", icon: "folder_open" },
  { href: "/dashboard/activity", label: "System Status", icon: "analytics" },
];

const bottomNavItems = [
  { href: "/dashboard/company/profile", label: "Company Profile", icon: "business" },
  { href: "/dashboard/company/credentials", label: "Credentials", icon: "badge" },
  { href: "#", label: "Help Center", icon: "help_outline" },
];

function NavIcon({ name }: { name: string }) {
  const icons: Record<string, React.ReactNode> = {
    dashboard: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
    folder_open: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
      </svg>
    ),
    analytics: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    business: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H4m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
    badge: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.829 2M9 14a3.978 3.978 0 01-.99-2.605V11a2 2 0 012-2h.01" />
      </svg>
    ),
    help_outline: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    logout: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
      </svg>
    ),
  };
  return icons[name] || null;
}

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "h-screen flex-shrink-0 sticky left-0 top-0 overflow-y-auto bg-[#FAF8FF] border-r border-[#434655]/15 flex flex-col gap-2 transition-all duration-300",
        collapsed ? "w-20 p-3" : "w-72 p-6"
      )}
    >
      <div className={cn("flex items-center", collapsed ? "justify-center" : "justify-between")}>
        {!collapsed && (
          <div className="mb-8">
            <h1 className="text-lg font-black text-[#131B2E] font-headline tracking-tighter">
              Enterprise Procurement
            </h1>
            <p className="text-xs text-[#434655] font-medium">AI-Powered Tendering</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "flex items-center justify-center w-9 h-9 rounded-lg bg-white border border-[#C3C6D7]/20 text-[#434655] hover:text-[#131B2E] hover:bg-slate-50 transition-all shadow-sm",
            collapsed && "mt-0"
          )}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg
            className={cn("w-4 h-4 transition-transform duration-300", collapsed && "rotate-180")}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>

      <nav className="flex-1 flex flex-col gap-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 font-medium text-sm transition-all duration-200 rounded-lg",
                isActive
                  ? "bg-white text-[#004AC6] font-semibold shadow-sm shadow-[#131B2E]/5"
                  : "text-[#434655] hover:text-[#131B2E] hover:bg-slate-100",
                collapsed && "justify-center px-0"
              )}
              title={collapsed ? item.label : undefined}
            >
              <NavIcon name={item.icon} />
              {!collapsed && item.label}
            </Link>
          );
        })}
      </nav>

      <Link
        href="/dashboard/tenders/new"
        className={cn(
          "bg-gradient-to-r from-[#004AC6] to-[#2563EB] text-white py-3 rounded-xl font-bold text-sm shadow-md transition-transform active:scale-95 text-center",
          collapsed ? "px-0 justify-center" : "px-4"
        )}
        title={collapsed ? "New Tender Request" : undefined}
      >
        {!collapsed ? "New Tender Request" : (
          <svg className="w-5 h-5 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        )}
      </Link>

      <div className={cn("mt-4 pt-4 border-t border-[#C3C6D7]/15 flex flex-col gap-1", collapsed && "items-center")}>
        {bottomNavItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-4 py-2 text-[#434655] text-sm hover:text-[#131B2E] transition-colors",
              collapsed && "justify-center px-0"
            )}
            title={collapsed ? item.label : undefined}
          >
            <NavIcon name={item.icon} />
            {!collapsed && item.label}
          </Link>
        ))}
        <button
          className={cn(
            "flex items-center gap-3 px-4 py-2 text-[#434655] text-sm hover:text-[#131B2E] transition-colors w-full",
            collapsed && "justify-center px-0"
          )}
          title={collapsed ? "Log Out" : undefined}
        >
          <NavIcon name="logout" />
          {!collapsed && "Log Out"}
        </button>
      </div>
    </aside>
  );
}
