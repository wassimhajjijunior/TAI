"use client";

import { DragEvent, useEffect, useRef, useState } from "react";
import { Activity, FileUp, FileText, LoaderCircle, ShieldCheck } from "lucide-react";
import {
  deleteTender,
  getTenders,
  uploadTender,
} from "@/lib/api/tenders";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { Tender } from "@/types";

const acceptedMimeTypes = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];

const acceptedExtensions = [".pdf", ".doc", ".docx", ".txt"];
const maxFileSizeBytes = 20 * 1024 * 1024;

function formatSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isSupportedType(file: File): boolean {
  const lowerName = file.name.toLowerCase();
  const hasSupportedExtension = acceptedExtensions.some((extension) => lowerName.endsWith(extension));
  return acceptedMimeTypes.includes(file.type) || hasSupportedExtension;
}

export function DocumentUploadDropzone() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [uploaded, setUploaded] = useState<Tender | null>(null);
  const [documents, setDocuments] = useState<Tender[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true);
  const [documentsError, setDocumentsError] = useState("");
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const isMountedRef = useRef(true);

  async function loadDocuments() {
    if (!isMountedRef.current) return;
    
    setIsLoadingDocuments(true);
    setDocumentsError("");

    try {
      const response = await getTenders({ page: 1, page_size: 50 });
      if (isMountedRef.current) {
        setDocuments(response.items || []);
      }
    } catch (error) {
      if (isMountedRef.current) {
        setDocumentsError(error instanceof Error ? error.message : "Failed to load documents");
      }
    } finally {
      if (isMountedRef.current) {
        setIsLoadingDocuments(false);
      }
    }
  }

  async function onDeleteDocument(documentId: string) {
    setDeletingDocumentId(documentId);
    setDocumentsError("");

    try {
      await deleteTender(documentId);
      setDocuments((prev) => prev.filter((item) => item.id !== documentId));
      if (uploaded?.id === documentId) {
        setUploaded(null);
      }
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : "Failed to delete document");
    } finally {
      setDeletingDocumentId(null);
    }
  }

  useEffect(() => {
    loadDocuments();
    
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  async function processFile(file: File) {
    if (!isSupportedType(file)) {
      setErrorMessage("Unsupported file type. Please upload PDF, DOC, DOCX or TXT.");
      return;
    }

    if (file.size > maxFileSizeBytes) {
      setErrorMessage("File too large. Maximum allowed size is 20 MB.");
      return;
    }

    setErrorMessage("");
    setUploaded(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await uploadTender(formData);
      setUploaded(result);
      setDocuments((prev) => [result, ...prev.filter((item) => item.id !== result.id)]);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (error) {
      setUploaded(null);
      setErrorMessage(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setIsUploading(false);
      setIsDragging(false);
    }
  }

  function openFileDialog() {
    inputRef.current?.click();
  }

  function onDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (!isUploading) {
      setIsDragging(true);
    }
  }

  function onDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (isUploading) return;

    const file = event.dataTransfer.files?.[0];
    if (!file) {
      setErrorMessage("No file detected.");
      return;
    }

    processFile(file);
  }

  const hasProcessingDocuments = documents.some((item) => 
    ["reading", "indexing", "qualifying", "generating"].includes(item.status)
  );

  return (
    <div className="grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
      <Card className="border-primary/20 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <FileUp className="size-4 text-primary" />
            Upload tender document
          </CardTitle>
          <CardDescription>
            Drag and drop your file or select from your device.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            className={cn(
              "group relative rounded-xl border-2 border-dashed p-8 transition cursor-pointer",
              "bg-gradient-to-b from-background to-muted/30",
              isDragging ? "border-primary bg-primary/5" : "border-border",
              isUploading ? "pointer-events-none opacity-70" : "hover:border-primary/50",
            )}
            onClick={openFileDialog}
            role="button"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openFileDialog();
              }
            }}
          >
            <div className="mx-auto flex max-w-sm flex-col items-center gap-3 text-center">
              <div className="rounded-full border border-primary/20 bg-primary/10 p-3 text-primary">
                <FileUp className="size-5" />
              </div>
              <p className="text-sm font-medium">Drop files here or click to browse</p>
              <p className="text-xs text-muted-foreground">Accepted: PDF, DOC, DOCX, TXT · Max 20 MB</p>
              <Badge variant="outline">Upload</Badge>
            </div>
          </div>

          <input
            ref={inputRef}
            type="file"
            hidden
            accept=".pdf,.doc,.docx,.txt"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (!file || isUploading) return;
              processFile(file);
            }}
          />

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{isUploading ? "Uploading (in progress)" : uploaded ? "Upload completed" : "Waiting for file"}</span>
              <span>{isUploading ? "..." : "100%"}</span>
            </div>
            <Progress value={isUploading ? 100 : 0} />
          </div>

          {errorMessage ? (
            <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {errorMessage}
            </p>
          ) : null}
        </CardContent>
        <CardFooter className="justify-end">
          <Button type="button" variant="outline" onClick={openFileDialog} disabled={isUploading}>
            {isUploading ? <LoaderCircle className="mr-2 size-4 animate-spin" /> : <FileUp className="mr-2 size-4" />}
            {isUploading ? "Uploading..." : "Select file"}
          </Button>
        </CardFooter>
      </Card>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="size-4 text-primary" />
            Upload summary
          </CardTitle>
          <CardDescription>Latest upload information.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {uploaded ? (
            <>
              <div className="rounded-lg border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">Document ID</p>
                <p className="font-mono text-xs">{uploaded.id}</p>
              </div>
              <div className="flex items-center gap-2 rounded-lg border bg-background p-3">
                <FileText className="size-4 text-primary" />
                <div>
                  <p className="text-sm font-medium">{uploaded.filename}</p>
                  <p className="text-xs text-muted-foreground">{formatSize(uploaded.file_size || 0)}</p>
                </div>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status</span>
                <Badge>{uploaded.status}</Badge>
              </div>
            </>
          ) : (
            <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
              No upload yet. Your first uploaded file metadata will appear here.
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="size-4 text-primary" />
            Existing files in database
          </CardTitle>
          <CardDescription>
            Files already uploaded and stored.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {isLoadingDocuments ? <p className="text-sm text-muted-foreground">Loading files...</p> : null}

          {documentsError ? (
            <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {documentsError}
            </p>
          ) : null}

          {!isLoadingDocuments && !documentsError && documents.length === 0 ? (
            <p className="rounded-lg border border-dashed p-5 text-sm text-muted-foreground">No files in database yet.</p>
          ) : null}

          {!isLoadingDocuments && !documentsError && documents.length > 0 ? (
            <div className="space-y-2">
              {documents.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-lg border bg-card p-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{item.filename}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatSize(item.file_size || 0)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={item.status === "failed" ? "destructive" : "secondary"}>{item.status}</Badge>
                    <Button
                      type="button"
                      size="sm"
                      variant="destructive"
                      disabled={deletingDocumentId !== null}
                      onClick={() => onDeleteDocument(item.id)}
                    >
                      {deletingDocumentId === item.id ? "Deleting..." : "Delete"}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </CardContent>
        <CardFooter className="justify-end">
          <Button type="button" variant="outline" onClick={loadDocuments} disabled={isLoadingDocuments}>
            Refresh list
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}