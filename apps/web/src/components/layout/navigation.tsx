"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type NavItem = {
  href: string;
  label: string;
};

const navItems: NavItem[] = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/documents/new", label: "New document" },
  { href: "/login", label: "Login" },
  { href: "/register", label: "Register" },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav>
      <ul className="flex items-center gap-2">
        {navItems.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className={cn(
                "inline-flex rounded-full px-2 py-1 text-sm text-muted-foreground transition-colors hover:text-foreground",
                pathname === item.href && "bg-secondary text-secondary-foreground"
              )}
            >
              {item.label}
              {item.href === "/documents/new" ? (
                <Badge variant="secondary" className="ml-2">
                  Track A
                </Badge>
              ) : null}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
