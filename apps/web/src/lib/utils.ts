import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

const DEFAULT_API_BASE_URL = "http://localhost:8100/api/v1";

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")}/api/v1`
    : DEFAULT_API_BASE_URL;
}

export function getApiWebSocketBaseUrl(): string {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8100";
  const normalized = apiBase.replace(/\/$/, "");
  if (normalized.startsWith("https://")) {
    return normalized.replace("https://", "wss://");
  }
  if (normalized.startsWith("http://")) {
    return normalized.replace("http://", "ws://");
  }
  return `ws://${normalized}`;
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    uploaded: "Uploaded",
    reading: "OCR",
    indexing: "Indexing",
    qualifying: "Qualification",
    qualified: "Qualified",
    generating: "Generating",
    completed: "Completed",
    failed: "Failed",
  };
  return labels[status] || status;
}

export function getStatusProgress(status: string): number {
  const progressMap: Record<string, number> = {
    uploaded: 10,
    reading: 30,
    indexing: 50,
    qualifying: 70,
    qualified: 85,
    generating: 95,
    completed: 100,
    failed: 0,
  };
  return progressMap[status] ?? 0;
}

export function formatDate(value: string | number | Date): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }
  return date.toLocaleDateString();
}

export function formatDateTime(value: string | number | Date): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }
  return date.toLocaleString();
}

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "-";
  }
  const units = ["B", "KB", "MB", "GB"];
  let index = 0;
  let value = bytes;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(1)} ${units[index]}`;
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
