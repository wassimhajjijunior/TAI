"use client";

import { useState, useEffect, useCallback } from "react";

interface UseApiOptions<T> {
  initialData?: T;
  autoFetch?: boolean;
}

interface UseApiReturn<T> {
  data: T | undefined;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: React.DependencyList = [],
  options: UseApiOptions<T> = {}
): UseApiReturn<T> {
  const { initialData, autoFetch = true } = options;
  const [data, setData] = useState<T | undefined>(initialData);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [autoFetch, fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function useTenderStatus(tenderId: string, initialStatus: string) {
  const [status, setStatus] = useState(initialStatus);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (["completed", "failed"].includes(status)) return;

    const interval = setInterval(async () => {
      try {
        const { getTender } = await import("@/lib/api/tenders");
        const tender = await getTender(tenderId);
        setStatus(tender.status);
        
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
        setProgress(progressMap[tender.status] || 0);
      } catch (err) {
        console.error("Failed to poll tender status:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [tenderId, status]);

  return { status, progress };
}
