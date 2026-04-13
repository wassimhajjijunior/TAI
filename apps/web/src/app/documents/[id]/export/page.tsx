"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { exportGeneratedResponse, type ExportResponse } from "@/lib/api/client";

export default function DocumentExportPage() {
  const params = useParams<{ id: string }>();
  const documentId = params?.id ?? "";

  const [responseId, setResponseId] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState("");
  const [exportResult, setExportResult] = useState<ExportResponse | null>(null);

  async function onExport() {
    if (!responseId.trim() || !documentId) {
      return;
    }
    setIsExporting(true);
    setError("");
    try {
      const response = await exportGeneratedResponse(documentId, responseId.trim());
      setExportResult(response);
    } catch (exportError) {
      setError(exportError instanceof Error ? exportError.message : "Export failed");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <section className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Track B · Export Response</CardTitle>
          <CardDescription>Export generated response to DOCX for this document.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            value={responseId}
            onChange={(event) => setResponseId(event.target.value)}
            placeholder="Paste response ID"
          />
          <Button type="button" disabled={!responseId.trim() || isExporting} onClick={() => void onExport()}>
            {isExporting ? "Exporting..." : "Export DOCX"}
          </Button>

          {error ? (
            <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          ) : null}

          {exportResult ? (
            <div className="rounded-lg border border-primary/30 bg-primary/5 p-3 text-sm">
              <p className="font-medium">Export ready</p>
              <a
                className="text-primary underline"
                href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8100"}${exportResult.download_url}`}
                target="_blank"
                rel="noreferrer"
              >
                Download DOCX
              </a>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}
