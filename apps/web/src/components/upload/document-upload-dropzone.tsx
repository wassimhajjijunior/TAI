"use client";

import { DragEvent, useEffect, useMemo, useRef, useState } from "react";
import { Activity, FileUp, FileText, LoaderCircle, ShieldCheck } from "lucide-react";
import {
  deleteDocument,
  fetchDocuments,
  fetchMessagingStatus,
  getApiWebSocketBaseUrl,
  getStatusProgress,
  uploadDocument,
  type MessagingStatus,
  type UploadedDocument,
} from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

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
  const [uploaded, setUploaded] = useState<UploadedDocument | null>(null);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true);
  const [documentsError, setDocumentsError] = useState("");
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [isTabVisible, setIsTabVisible] = useState(true);
  const [messagingStatus, setMessagingStatus] = useState<MessagingStatus | null>(null);
  const [isLoadingMessaging, setIsLoadingMessaging] = useState(true);
  const [messagingError, setMessagingError] = useState("");
  const isMessagingRequestInFlightRef = useRef(false);
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);

  async function loadDocuments(options?: { silent?: boolean }) {
    const silent = options?.silent ?? false;

    if (!isMountedRef.current) {
      return;
    }
    if (!silent) {
      setIsLoadingDocuments(true);
      setDocumentsError("");
    }

    try {
      const items = await fetchDocuments();
      if (isMountedRef.current) {
        setDocuments(items);
      }
    } catch (error) {
      if (isMountedRef.current) {
        setDocumentsError(error instanceof Error ? error.message : "Failed to load documents");
      }
    } finally {
      if (isMountedRef.current && !silent) {
        setIsLoadingDocuments(false);
      }
    }
  }

  async function onDeleteDocument(documentId: string) {
    setDeletingDocumentId(documentId);
    setDocumentsError("");

    try {
      await deleteDocument(documentId);
      setDocuments((previous) => previous.filter((item) => item.id !== documentId));
      if (uploaded?.id === documentId) {
        setUploaded(null);
      }
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : "Failed to delete document");
    } finally {
      setDeletingDocumentId(null);
    }
  }

  async function loadMessagingStatus(options?: { silent?: boolean }) {
    const silent = options?.silent ?? false;

    if (!isMountedRef.current) {
      return;
    }

    if (isMessagingRequestInFlightRef.current) {
      return;
    }

    isMessagingRequestInFlightRef.current = true;

    if (!silent) {
      setIsLoadingMessaging(true);
      setMessagingError("");
    }

    try {
      const status = await fetchMessagingStatus();
      if (isMountedRef.current) {
        setMessagingStatus(status);
      }
    } catch (error) {
      if (isMountedRef.current) {
        setMessagingError(error instanceof Error ? error.message : "Failed to load messaging status");
      }
    } finally {
      isMessagingRequestInFlightRef.current = false;
      if (isMountedRef.current && !silent) {
        setIsLoadingMessaging(false);
      }
    }
  }

  const uploadProgress = useMemo(() => (uploaded ? 100 : 0), [uploaded]);

  const hasProcessingDocuments = useMemo(
    () => documents.some((item) => item.status === "ocr_processing"),
    [documents]
  );

  useEffect(() => {
    void loadDocuments();
    void loadMessagingStatus();

    const onVisibilityChange = () => {
      setIsTabVisible(document.visibilityState === "visible");
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      isMountedRef.current = false;
      if (reconnectTimeoutRef.current !== null) {
        window.clearTimeout(reconnectTimeoutRef.current);
      }
      websocketRef.current?.close();
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, []);

  useEffect(() => {
    let isDisposed = false;

    const connect = () => {
      if (isDisposed || !isMountedRef.current) {
        return;
      }

      const ws = new WebSocket(`${getApiWebSocketBaseUrl()}/api/v1/live/documents`);
      websocketRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as {
            type?: string;
            items?: UploadedDocument[];
          };
          if (payload.type === "documents.updated" && Array.isArray(payload.items) && isMountedRef.current) {
            setDocuments(payload.items);
            setIsLoadingDocuments(false);
            setDocumentsError("");
          }
        } catch {
        }
      };

      ws.onclose = () => {
        if (isDisposed || !isMountedRef.current) {
          return;
        }
        reconnectTimeoutRef.current = window.setTimeout(connect, 2000);
      };
    };

    connect();

    return () => {
      isDisposed = true;
      if (reconnectTimeoutRef.current !== null) {
        window.clearTimeout(reconnectTimeoutRef.current);
      }
      websocketRef.current?.close();
    };
  }, []);

  useEffect(() => {
    if (!hasProcessingDocuments || !isTabVisible) {
      return;
    }

    const interval = window.setInterval(() => {
      void loadDocuments({ silent: true });
    }, 3000);

    return () => {
      window.clearInterval(interval);
    };
  }, [hasProcessingDocuments, isTabVisible]);

  useEffect(() => {
    if (!hasProcessingDocuments || !isTabVisible) {
      return;
    }

    const interval = window.setInterval(() => {
      void loadMessagingStatus({ silent: true });
    }, 15000);

    return () => {
      window.clearInterval(interval);
    };
  }, [hasProcessingDocuments, isTabVisible]);

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
      const result = await uploadDocument(file);
      setUploaded(result);
      setDocuments((previous) => [result, ...previous.filter((item) => item.id !== result.id)]);
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

  function onDragOver(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    if (!isUploading) {
      setIsDragging(true);
    }
  }

  function onDragLeave(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setIsDragging(false);
  }

  function onDrop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    if (isUploading) {
      return;
    }

    const file = event.dataTransfer.files?.[0];
    if (!file) {
      setErrorMessage("No file detected.");
      return;
    }

    void processFile(file);
  }

  return (
    <div className="grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
      <Card className="border-primary/20 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <FileUp className="size-4 text-primary" />
            Upload tender document
          </CardTitle>
          <CardDescription>
            Drag & drop your file or select from your device. This starts Track A ingestion flow.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <button
            type="button"
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            className={cn(
              "group relative rounded-xl border-2 border-dashed p-8 transition",
              "bg-gradient-to-b from-background to-muted/30",
              isDragging ? "border-primary bg-primary/5" : "border-border",
              isUploading ? "pointer-events-none opacity-70" : "cursor-pointer hover:border-primary/50",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            )}
            onClick={openFileDialog}
            aria-label="Drop file here or open file selector"
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openFileDialog();
              }
            }}
            disabled={isUploading}
          >
            <div className="mx-auto flex max-w-sm flex-col items-center gap-3 text-center">
              <div className="rounded-full border border-primary/20 bg-primary/10 p-3 text-primary">
                <FileUp className="size-5" />
              </div>
              <p className="text-sm font-medium">Drop files here or click to browse</p>
              <p className="text-xs text-muted-foreground">Accepted: PDF, DOC, DOCX, TXT · Max 20 MB</p>
              <Badge variant="outline">Step 1 · Intake</Badge>
            </div>
          </button>

          <input
            ref={inputRef}
            type="file"
            hidden
            accept=".pdf,.doc,.docx,.txt,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (!file || isUploading) {
                return;
              }
              void processFile(file);
            }}
          />

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{isUploading ? "Uploading (in progress)" : uploaded ? "Upload completed" : "Waiting for file"}</span>
              <span>{isUploading ? "..." : `${uploadProgress}%`}</span>
            </div>
            <Progress value={uploadProgress} />
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
          <CardDescription>Latest upload information saved from API response.</CardDescription>
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
                  <p className="text-xs text-muted-foreground">{formatSize(uploaded.size_bytes)} · {uploaded.content_type}</p>
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
            Messaging & pipeline status
          </CardTitle>
          <CardDescription>
            RabbitMQ connectivity and Track A event flow used by OCR and downstream services.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {isLoadingMessaging ? <p className="text-sm text-muted-foreground">Loading messaging status...</p> : null}

          {messagingError ? (
            <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {messagingError}
            </p>
          ) : null}

          {!isLoadingMessaging && !messagingError && messagingStatus ? (
            <>
              <div className="flex flex-wrap items-center gap-2 rounded-lg border bg-muted/20 p-3 text-sm">
                <span className="text-muted-foreground">Broker connectivity</span>
                <Badge variant={messagingStatus.rabbitmq.connected ? "default" : "destructive"}>
                  {messagingStatus.rabbitmq.connected ? "Connected" : "Disconnected"}
                </Badge>
                <span className="text-xs text-muted-foreground">{messagingStatus.rabbitmq.detail}</span>
              </div>

              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground">Exchange</p>
                <p className="font-mono text-xs">
                  {messagingStatus.topology.exchange} ({messagingStatus.topology.exchange_type})
                </p>
              </div>

              <div className="rounded-lg border p-3">
                <p className="mb-2 text-xs text-muted-foreground">Event flow</p>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  {messagingStatus.topology.event_flow.map((event, index) => (
                    <div key={event} className="flex items-center gap-2">
                      <Badge variant="secondary">{event}</Badge>
                      {index < messagingStatus.topology.event_flow.length - 1 ? (
                        <span className="text-muted-foreground">→</span>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : null}
        </CardContent>
        <CardFooter className="justify-end">
          <Button type="button" variant="outline" onClick={() => void loadMessagingStatus()} disabled={isLoadingMessaging}>
            Refresh messaging
          </Button>
        </CardFooter>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-base">Existing files in database</CardTitle>
          <CardDescription>
            Files already uploaded and stored in Supabase documents table.
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
                      {formatSize(item.size_bytes)} · {item.content_type}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={item.status === "ocr_failed" ? "destructive" : "secondary"}>{item.status}</Badge>
                    <div className="w-28">
                      <Progress value={getStatusProgress(item.status)} />
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="destructive"
                      disabled={deletingDocumentId !== null}
                      onClick={() => void onDeleteDocument(item.id)}
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
          <Button type="button" variant="outline" onClick={() => void loadDocuments()} disabled={isLoadingDocuments}>
            Refresh list
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
