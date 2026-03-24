const defaultApiBaseUrl = "http://localhost:8100";

export type UploadedDocument = {
  id: string;
  tenant_id?: string;
  filename: string;
  size_bytes: number;
  content_type: string;
  created_at: string;
  status: string;
};

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? defaultApiBaseUrl;
}

export async function fetchApiHealth(): Promise<{ status: string }> {
  const response = await fetch(`${getApiBaseUrl()}/health`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API health request failed with status ${response.status}`);
  }

  const data = (await response.json()) as { status: string };
  return data;
}

export async function uploadDocument(file: File): Promise<UploadedDocument> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${getApiBaseUrl()}/api/v1/documents`, {
    method: "POST",
    body: formData,
  });

  const payload = (await response.json()) as {
    detail?: string;
    document?: UploadedDocument;
  };

  if (!response.ok || !payload.document) {
    throw new Error(payload.detail ?? "Upload failed");
  }

  return payload.document;
}

export async function fetchDocuments(): Promise<UploadedDocument[]> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/documents`, {
    method: "GET",
    cache: "no-store",
  });

  const payload = (await response.json()) as {
    detail?: string;
    items?: UploadedDocument[];
  };

  if (!response.ok || !payload.items) {
    throw new Error(payload.detail ?? "Failed to load documents");
  }

  return payload.items;
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/documents/${documentId}`, {
    method: "DELETE",
  });

  if (response.ok) {
    return;
  }

  const payload = (await response.json()) as {
    detail?: string;
  };

  throw new Error(payload.detail ?? "Failed to delete document");
}
