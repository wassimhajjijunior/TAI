"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface Tab {
  id: string;
  label: string;
  badge?: string | number;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onTabChange, className }: TabsProps) {
  return (
    <div className={cn("flex border-b border-[#C3C6D7]/20", className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            "px-6 py-3 text-sm font-semibold transition-colors relative",
            activeTab === tab.id
              ? "text-[#004AC6] border-b-2 border-[#004AC6]"
              : "text-[#434655] hover:text-[#131B2E]"
          )}
        >
          {tab.label}
          {tab.badge !== undefined && (
            <span className="ml-2 px-1.5 py-0.5 text-[10px] bg-[#EAEDFF] rounded-full">
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

interface TabPanelProps {
  children: React.ReactNode;
  isActive: boolean;
}

export function TabPanel({ children, isActive }: TabPanelProps) {
  if (!isActive) return null;
  return <div className="py-6">{children}</div>;
}
