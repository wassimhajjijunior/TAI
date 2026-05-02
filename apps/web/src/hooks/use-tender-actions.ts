"use client";

import { useState, useCallback } from "react";
import { deleteTender } from "@/lib/api/tenders";

export function useTenderActions() {
  const [loading, setLoading] = useState<string | null>(null);

  const handleDelete = useCallback(async (tenderId: string): Promise<boolean> => {
    setLoading(tenderId);
    try {
      await deleteTender(tenderId);
      return true;
    } catch (error) {
      console.error("Failed to delete tender:", error);
      return false;
    } finally {
      setLoading(null);
    }
  }, []);

  return { loading, deleteTender: handleDelete };
}

export function useTenderWorkspaceActions(tenderId: string) {
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const runQualificationCheck = useCallback(async () => {
    setActionLoading("qualification");
    try {
      const { runQualificationCheck: runCheck } = await import("@/lib/api/compliance");
      await runCheck(tenderId);
      return true;
    } catch (error) {
      console.error("Failed to run qualification check:", error);
      return false;
    } finally {
      setActionLoading(null);
    }
  }, [tenderId]);

  const generateResponse = useCallback(async () => {
    setActionLoading("response");
    try {
      const { generateDraftResponse } = await import("@/lib/api/responses");
      await generateDraftResponse(tenderId);
      return true;
    } catch (error) {
      console.error("Failed to generate response:", error);
      return false;
    } finally {
      setActionLoading(null);
    }
  }, [tenderId]);

  const createExport = useCallback(async (type: "pdf" | "docx" | "xlsx") => {
    setActionLoading(`export-${type}`);
    try {
      const { createExport: create } = await import("@/lib/api/exports");
      await create(tenderId, type);
      return true;
    } catch (error) {
      console.error("Failed to create export:", error);
      return false;
    } finally {
      setActionLoading(null);
    }
  }, [tenderId]);

  return {
    actionLoading,
    runQualificationCheck,
    generateResponse,
    createExport,
  };
}
