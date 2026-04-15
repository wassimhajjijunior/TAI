"use client";

import { use } from "react";
import { useState, useEffect } from "react";
import { getExports, createExport, getExportDownloadUrl } from "@/lib/api/exports";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { formatDateTime } from "@/lib/utils";
import type { Export } from "@/types";

export default function ExportsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [exports, setExports] = useState<Export[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    const fetchExports = async () => {
      try {
        const response = await getExports(id);
        setExports(response.items);
      } catch (err) {
        console.error("Failed to load exports:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchExports();
  }, [id]);

  const handleCreateExport = async (type: "pdf" | "docx" | "xlsx") => {
    setCreating(type);
    try {
      const newExport = await createExport(id, type);
      setExports((prev) => [newExport, ...prev]);
    } catch (err) {
      console.error("Failed to create export:", err);
    } finally {
      setCreating(null);
    }
  };

  const handleDownload = async (exportItem: Export) => {
    setDownloading(exportItem.id);
    try {
      const url = getExportDownloadUrl(exportItem.id);
      window.open(url, "_blank");
    } catch (err) {
      console.error("Failed to download export:", err);
    } finally {
      setDownloading(null);
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "error";
      case "processing":
        return "warning";
      case "pending":
        return "info";
      default:
        return "default";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "pdf":
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case "docx":
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
      case "xlsx":
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold font-headline tracking-tight text-[#131B2E]">
            Export Documents
          </h1>
          <p className="text-[#434655] mt-1">Download tender responses in various formats</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { type: "pdf" as const, label: "PDF Document", desc: "Complete response with formatting" },
          { type: "docx" as const, label: "Word Document", desc: "Editable DOCX format" },
          { type: "xlsx" as const, label: "Excel Spreadsheet", desc: "Compliance checklist" },
        ].map((format) => (
          <Card key={format.type} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-[#EAEDFF] flex items-center justify-center text-[#004AC6]">
                  {getTypeIcon(format.type)}
                </div>
                <Badge variant="info" size="sm">{format.type.toUpperCase()}</Badge>
              </div>
              <h3 className="font-headline text-base font-bold text-[#131B2E] mb-1">{format.label}</h3>
              <p className="text-sm text-[#434655] mb-4">{format.desc}</p>
              <Button
                variant="secondary"
                size="sm"
                className="w-full"
                onClick={() => handleCreateExport(format.type)}
                disabled={creating === format.type}
              >
                {creating === format.type ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Creating...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Create Export
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card padding="none">
        <div className="p-6 border-b border-[#C3C6D7]/20">
          <h2 className="font-headline text-lg font-bold text-[#131B2E]">Export History</h2>
        </div>
        <div className="divide-y divide-[#C3C6D7]/20">
          {exports.length === 0 ? (
            <div className="p-6 text-center text-[#434655]">
              No exports yet. Create an export to download the response.
            </div>
          ) : (
            exports.map((exportItem) => (
              <div key={exportItem.id} className="p-4 flex items-center justify-between hover:bg-[#F2F3FF] transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[#EAEDFF] flex items-center justify-center text-[#004AC6]">
                    {getTypeIcon(exportItem.type)}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#131B2E]">{exportItem.filename}</p>
                    <p className="text-xs text-[#737686]">{formatDateTime(exportItem.created_at)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={getStatusVariant(exportItem.status)} size="sm">
                    {exportItem.status}
                  </Badge>
                  {exportItem.status === "completed" && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleDownload(exportItem)}
                      disabled={downloading === exportItem.id}
                    >
                      {downloading === exportItem.id ? (
                        <Spinner size="sm" />
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          Download
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}