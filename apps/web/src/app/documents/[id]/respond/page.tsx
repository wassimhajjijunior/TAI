"use client";

import { FormEvent, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  exportGeneratedResponse,
  generateTenderResponse,
  ragQuery,
  type ExportResponse,
  type GeneratedResponse,
  type RagSearchResult,
} from "@/lib/api/client";

export default function DocumentRespondPage() {
  const params = useParams<{ id: string }>();
  const documentId = params?.id ?? "";

  const [query, setQuery] = useState("Generate a complete response for this tender document.");
  const [isRetrieving, setIsRetrieving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [results, setResults] = useState<RagSearchResult[]>([]);
  const [generated, setGenerated] = useState<GeneratedResponse | null>(null);
  const [exportResult, setExportResult] = useState<ExportResponse | null>(null);
  const [error, setError] = useState("");

  const canRun = useMemo(() => Boolean(documentId && query.trim()), [documentId, query]);

  async function onRetrieve(event: FormEvent) {
    event.preventDefault();
    if (!canRun) {
      return;
    }
    setIsRetrieving(true);
    setError("");
    setExportResult(null);
    try {
      const response = await ragQuery(documentId, query.trim(), 8);
      setResults(response.results);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "RAG retrieval failed");
    } finally {
      setIsRetrieving(false);
    }
  }

  async function onGenerate() {
    if (!canRun) {
      return;
    }
    setIsGenerating(true);
    setError("");
    setExportResult(null);
    try {
      const response = await generateTenderResponse(documentId, query.trim());
      setGenerated(response);
    } catch (generateError) {
      setError(generateError instanceof Error ? generateError.message : "Generation failed");
    } finally {
      setIsGenerating(false);
    }
  }

  async function onExport() {
    if (!generated) {
      return;
    }
    setIsExporting(true);
    setError("");
    try {
      const response = await exportGeneratedResponse(documentId, generated.id);
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
          <CardTitle className="text-xl">Track B · RAG Chat Workspace</CardTitle>
          <CardDescription>
            Retrieve relevant chunks with RAG, generate a response, then export DOCX.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form className="space-y-3" onSubmit={onRetrieve}>
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ask a generation question..."
            />
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={!canRun || isRetrieving || isGenerating}>
                {isRetrieving ? "Retrieving..." : "Retrieve context"}
              </Button>
              <Button type="button" variant="outline" disabled={!canRun || isGenerating} onClick={() => void onGenerate()}>
                {isGenerating ? "Generating..." : "Generate response"}
              </Button>
              <Button type="button" variant="secondary" disabled={!generated || isExporting} onClick={() => void onExport()}>
                {isExporting ? "Exporting..." : "Export DOCX"}
              </Button>
            </div>
          </form>

          {error ? (
            <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Retrieved chunks</CardTitle>
          <CardDescription>Top context pieces returned by vector similarity search.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {results.length === 0 ? <p className="text-sm text-muted-foreground">No retrieval yet.</p> : null}
          {results.map((item) => (
            <div key={item.id} className="rounded-lg border p-3">
              <div className="mb-2 flex items-center gap-2">
                <Badge variant="secondary">Pos {item.position}</Badge>
                <Badge variant="outline">Sim {item.similarity.toFixed(3)}</Badge>
              </div>
              <p className="text-sm text-muted-foreground">{item.content_translated ?? item.content}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Generated response</CardTitle>
          <CardDescription>LLM output grounded on retrieved chunks.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {!generated ? <p className="text-sm text-muted-foreground">No generated response yet.</p> : null}
          {generated ? (
            <>
              <div className="rounded-lg border p-3">
                <p className="mb-2 text-xs text-muted-foreground">Response ID</p>
                <p className="font-mono text-xs">{generated.id}</p>
              </div>
              <Separator />
              <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap rounded-lg border bg-muted/20 p-3 text-sm">
                {generated.content}
              </pre>
            </>
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
