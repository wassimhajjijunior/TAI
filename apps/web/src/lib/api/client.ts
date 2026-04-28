import { getApiBaseUrl, getApiWebSocketBaseUrl, getStatusProgress } from "@/lib/utils";
import {
  type ActivityLog,
  type CompanyProfile,
  type ComplianceRequirement,
  type ComplianceScore,
  type DraftResponse,
  type Export,
  type PaginatedResponse,
  type RAGMessage,
  type SystemHealth,
  type Tender,
} from "@/types";
import type { APIError } from "@/types";

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | undefined>;
}

const MOCK_MODE = process.env.NEXT_PUBLIC_MOCK_MODE === "true";

const mockTenders: Tender[] = [
  {
    id: "tender-001",
    filename: "AO_Construction_Medina_2026.pdf",
    status: "completed",
    created_at: "2026-04-10T10:12:00Z",
    updated_at: "2026-04-12T15:30:00Z",
    page_count: 82,
    file_size: 12_400_000,
    metadata: {
      title: "Construction de la médina technologique",
      authority: "Ministère de l'Équipement",
      reference_number: "AO-2026-MLN-552",
      submission_date: "2026-05-12T10:00:00Z",
      risk_rating: "moderate",
    },
  },
  {
    id: "tender-002",
    filename: "AO_Smart_Grid_Regional.pdf",
    status: "generating",
    created_at: "2026-04-14T09:25:00Z",
    updated_at: "2026-04-15T08:10:00Z",
    page_count: 54,
    file_size: 9_820_000,
  },
  {
    id: "tender-003",
    filename: "AO_EduTech_Platform_2026.pdf",
    status: "qualified",
    created_at: "2026-04-08T13:40:00Z",
    updated_at: "2026-04-09T18:05:00Z",
    page_count: 36,
    file_size: 5_120_000,
  },
];

const mockComplianceRequirements: ComplianceRequirement[] = [
  {
    id: "req-001",
    tender_id: "tender-001",
    clause: "Section 2.1 – Capacité financière",
    requirement: "Fournir un bilan certifié des 3 dernières années.",
    status: "met",
    evidence: "Bilans 2023-2025 transmis.",
    created_at: "2026-04-12T10:00:00Z",
  },
  {
    id: "req-002",
    tender_id: "tender-001",
    clause: "Section 3.4 – Références",
    requirement: "Au moins 2 projets similaires réalisés.",
    status: "review",
    evidence: "Projet Smart City (2024), Data Center (2023).",
    created_at: "2026-04-12T10:02:00Z",
  },
  {
    id: "req-003",
    tender_id: "tender-001",
    clause: "Section 5 – Garantie",
    requirement: "Garantie bancaire de soumission.",
    status: "unmet",
    created_at: "2026-04-12T10:03:00Z",
  },
];

const mockComplianceScore: ComplianceScore = {
  id: "score-001",
  eligibility_score: 84,
  total_requirements: 12,
  met_requirements: 9,
  recommendation: "Review",
  go_no_go: "review",
};

const mockRagMessages: RAGMessage[] = [
  {
    id: "rag-001",
    tender_id: "tender-001",
    role: "user",
    content: "Quelle est la date limite de remise ?",
    created_at: "2026-04-12T11:00:00Z",
  },
  {
    id: "rag-002",
    tender_id: "tender-001",
    role: "assistant",
    content: "La date limite est le 12 mai 2026 à 10h00.",
    sources: [
      {
        page: 4,
        section: "Conditions générales",
        excerpt: "La date limite de remise des offres est fixée au 12/05/2026 à 10h00.",
        relevance: 0.92,
      },
    ],
    created_at: "2026-04-12T11:01:00Z",
  },
];

const mockDraftResponses: DraftResponse[] = [
  {
    id: "resp-001",
    tender_id: "tender-001",
    filename: "Réponse AO – Construction médina v1",
    content: "## Présentation\nNotre entreprise propose une solution clé en main...",
    version: 1,
    created_at: "2026-04-12T14:00:00Z",
    updated_at: "2026-04-12T16:45:00Z",
  },
  {
    id: "resp-002",
    tender_id: "tender-001",
    filename: "Réponse AO – Construction médina v2",
    content: "## Approche technique\nNous déployons un phasage...",
    version: 2,
    created_at: "2026-04-13T09:30:00Z",
    updated_at: "2026-04-13T11:20:00Z",
  },
];

const mockExports: Export[] = [
  {
    id: "exp-001",
    tender_id: "tender-001",
    type: "docx",
    status: "completed",
    filename: "Réponse_AO_Medina.docx",
    created_at: "2026-04-13T12:05:00Z",
    download_url: "#",
  },
  {
    id: "exp-002",
    tender_id: "tender-001",
    type: "pdf",
    status: "processing",
    filename: "Réponse_AO_Medina.pdf",
    created_at: "2026-04-13T12:30:00Z",
  },
];

const mockCompanyProfile: CompanyProfile = {
  id: "company-001",
  name: "NovaTech Engineering",
  description: "Integrated infrastructure and smart systems contractor.",
  website: "https://novatech.tn",
  contact_email: "contact@novatech.tn",
  contact_phone: "+216 71 000 000",
  address: "Avenue Habib Bourguiba, Tunis",
  created_at: "2026-03-01T08:00:00Z",
  updated_at: "2026-04-10T10:00:00Z",
};

const mockSystemHealth: SystemHealth = {
  status: "healthy",
  services: {
    database: { status: "up", latency_ms: 32 },
    rabbitmq: { status: "up", latency_ms: 21 },
    redis: { status: "up", latency_ms: 12 },
  },
  checked_at: "2026-04-15T08:00:00Z",
};

const mockActivityLogs: ActivityLog[] = [
  {
    id: "act-001",
    tender_id: "tender-001",
    action: "OCR completed",
    details: "Document text extracted and stored.",
    created_at: "2026-04-12T09:10:00Z",
  },
  {
    id: "act-002",
    tender_id: "tender-001",
    action: "Embeddings generated",
    details: "Chunk embeddings saved to pgvector.",
    created_at: "2026-04-12T09:15:00Z",
  },
  {
    id: "act-003",
    tender_id: "tender-002",
    action: "Response drafting",
    details: "Draft response generation in progress.",
    created_at: "2026-04-15T08:15:00Z",
  },
];

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: APIError = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
      status_code: response.status,
    }));
    throw new Error(error.detail);
  }
  return response.json();
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const url = new URL(`${getApiBaseUrl()}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  return url.toString();
}

export const api = {
  async get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
    if (MOCK_MODE) {
      return mockGet(path, params) as T;
    }
    const response = await fetch(buildUrl(path, params), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return handleResponse<T>(response);
  },

  async post<T>(path: string, body?: unknown): Promise<T> {
    if (MOCK_MODE) {
      return mockPost(path, body) as T;
    }
    const response = await fetch(buildUrl(path), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(response);
  },

  async put<T>(path: string, body: unknown): Promise<T> {
    if (MOCK_MODE) {
      return mockPut(path, body) as T;
    }
    const response = await fetch(buildUrl(path), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return handleResponse<T>(response);
  },

  async delete<T>(path: string): Promise<T> {
    if (MOCK_MODE) {
      return mockDelete(path) as T;
    }
    const response = await fetch(buildUrl(path), {
      method: 'DELETE',
    });
    return handleResponse<T>(response);
  },

  async upload<T>(path: string, formData: FormData): Promise<T> {
    if (MOCK_MODE) {
      return mockUpload(path, formData) as T;
    }
    const response = await fetch(buildUrl(path), {
      method: 'POST',
      body: formData,
    });
    return handleResponse<T>(response);
  },
};

export type UploadedDocument = {
  id: string;
  filename: string;
  status: string;
  size_bytes: number;
  content_type: string;
  created_at: string;
};

export type MessagingStatus = {
  rabbitmq: {
    connected: boolean;
    detail: string;
  };
  topology: {
    exchange: string;
    exchange_type: string;
    event_flow: string[];
  };
};

export type RagSearchResult = {
  id: string;
  position: number;
  similarity: number;
  content: string;
  content_translated?: string;
  source_page?: number;
  source_section?: string;
};

export type GeneratedResponse = {
  id: string;
  tender_id: string;
  content: string;
  created_at: string;
};

export type ExportResponse = {
  id: string;
  download_url: string;
  status: "completed" | "processing" | "failed";
};

export async function fetchDocuments(): Promise<UploadedDocument[]> {
  if (MOCK_MODE) {
    return mockTenders.map((tender) => ({
      id: tender.id,
      filename: tender.filename,
      status: tender.status,
      size_bytes: tender.file_size ?? 0,
      content_type: "application/pdf",
      created_at: tender.created_at,
    }));
  }
  const response = await api.get<{ items: UploadedDocument[] }>("/documents");
  return response.items;
}

export async function uploadDocument(file: File): Promise<UploadedDocument> {
  if (MOCK_MODE) {
    return {
      id: "tender-004",
      filename: file.name,
      status: "uploaded",
      size_bytes: file.size,
      content_type: file.type || "application/pdf",
      created_at: new Date().toISOString(),
    };
  }
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.upload<{ document: UploadedDocument }>("/documents", formData);
  return response.document;
}

export async function deleteDocument(documentId: string): Promise<void> {
  if (MOCK_MODE) {
    return;
  }
  await api.delete(`/documents/${documentId}`);
}

export async function fetchApiHealth(): Promise<{ status: string }> {
  if (MOCK_MODE) {
    return { status: "healthy" };
  }
  return api.get<{ status: string }>("/system/health");
}

export async function fetchDocumentOcrArtifact(documentId: string): Promise<unknown> {
  if (MOCK_MODE) {
    return {
      document_id: documentId,
      text_excerpt: "Mock OCR artifact preview",
    };
  }
  const response = await api.get<{ artifact: unknown }>(`/documents/${documentId}/ocr-artifact`);
  return response.artifact;
}

export async function fetchMessagingStatus(): Promise<MessagingStatus> {
  if (MOCK_MODE) {
    return {
      rabbitmq: { connected: true, detail: "Mock broker" },
      topology: {
        exchange: "p2m.events",
        exchange_type: "topic",
        event_flow: [
          "document_uploaded",
          "ocr_complete",
          "nlp_completed",
          "embedding_complete",
          "compliance_completed",
          "llm_generation",
          "generation_complete",
          "export_complete",
        ],
      },
    };
  }

  const response = await api.get<{ rabbitmq: { connected: boolean; detail: string }; topology: { exchange: string; exchange_type: string; event_flow: string[] } }>("/system/messaging/topology");
  return {
    rabbitmq: response.rabbitmq,
    topology: response.topology,
  };
}

export async function ragQuery(
  documentId: string,
  query: string,
  topK = 8
): Promise<{ answer: string; results: RagSearchResult[] }> {
  if (MOCK_MODE) {
    const results = mockRagMessages[1]?.sources?.map((source, index) => ({
      id: `rag-result-${index + 1}`,
      position: index + 1,
      similarity: 0.92 - index * 0.03,
      content: source.excerpt,
      source_page: source.page,
      source_section: source.section,
    })) ?? [];
    return {
      answer: "La date limite est le 12 mai 2026 à 10h00.",
      results,
    };
  }
  return api.post<{ answer: string; results: RagSearchResult[] }>("/rag/query", {
    document_id: documentId,
    query,
    top_k: topK,
  });
}

export async function generateTenderResponse(
  documentId: string,
  prompt: string
): Promise<GeneratedResponse> {
  if (MOCK_MODE) {
    return {
      id: "generated-001",
      tender_id: documentId,
      content: `## Réponse générée\n\n${prompt}\n\nNotre équipe propose une approche phasée avec un plan qualité détaillé.`,
      created_at: new Date().toISOString(),
    };
  }
  return api.post<GeneratedResponse>(`/documents/${documentId}/responses/generate`, { prompt });
}

export async function exportGeneratedResponse(
  documentId: string,
  responseId: string
): Promise<ExportResponse> {
  if (MOCK_MODE) {
    return {
      id: "export-001",
      download_url: `/exports/${responseId}/download`,
      status: "completed",
    };
  }
  return api.post<ExportResponse>(`/documents/${documentId}/export`, { response_id: responseId, type: "docx" });
}

function mockGet(path: string, params?: Record<string, string | number | undefined>) {
  if (path.startsWith("/documents") && path.split("/").length === 2) {
    return {
      items: mockTenders,
      total: mockTenders.length,
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 10,
    } as PaginatedResponse<Tender>;
  }

  if (path.startsWith("/documents/") && path.endsWith("/compliance")) {
    return mockComplianceRequirements;
  }

  if (path.startsWith("/documents/") && path.endsWith("/compliance/score")) {
    return mockComplianceScore;
  }

  if (path.startsWith("/documents/") && path.endsWith("/rag/history")) {
    return mockRagMessages;
  }

  if (path.startsWith("/documents/") && path.endsWith("/responses")) {
    return mockDraftResponses;
  }

  if (path.startsWith("/documents/") && path.endsWith("/exports")) {
    return {
      items: mockExports,
      total: mockExports.length,
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 10,
    } as PaginatedResponse<Export>;
  }

  if (path === "/company/profile") {
    return mockCompanyProfile;
  }

  if (path === "/system/health") {
    return mockSystemHealth;
  }

  if (path === "/system/activity") {
    return {
      items: mockActivityLogs,
      total: mockActivityLogs.length,
    } as PaginatedResponse<ActivityLog>;
  }

  if (path.startsWith("/documents/")) {
    const id = path.split("/")[2];
    return mockTenders.find((tender) => tender.id === id) || mockTenders[0];
  }

  if (path === "/system/messaging/topology") {
    return {
      queues: [
        { name: "track_a.ocr.queue", messages: 0, consumers: 1 },
        { name: "track_a.nlp.queue", messages: 0, consumers: 1 },
      ],
      exchanges: [{ name: "p2m.events", type: "topic" }],
    };
  }

  if (path === "/system/ws") {
    return { url: getApiWebSocketBaseUrl() };
  }

  return {};
}

function mockPost(path: string, body?: unknown) {
  if (path === "/rag/query") {
    return {
      answer: "La date limite est le 12 mai 2026 à 10h00.",
      sources: mockRagMessages[1]?.sources || [],
      results: (mockRagMessages[1]?.sources || []).map((source, index) => ({
        id: `rag-result-${index + 1}`,
        position: index + 1,
        similarity: 0.92 - index * 0.03,
        content: source.excerpt,
        source_page: source.page,
        source_section: source.section,
      })),
    };
  }

  if (path.endsWith("/responses/generate")) {
    return mockDraftResponses[0];
  }

  if (path.endsWith("/compliance/check")) {
    return { status: "ok" };
  }

  if (path.endsWith("/export")) {
    return mockExports[0];
  }

  return { status: "ok" };
}

function mockPut(path: string, body?: unknown) {
  if (path === "/company/profile") {
    return { ...mockCompanyProfile, ...(body as Partial<CompanyProfile>) };
  }

  if (path.includes("/compliance/")) {
    const updated = { ...mockComplianceRequirements[0], ...(body as Partial<ComplianceRequirement>) };
    return updated;
  }

  if (path.includes("/responses/")) {
    return { ...mockDraftResponses[0], ...(body as Partial<DraftResponse>) };
  }

  return { status: "ok" };
}

function mockDelete(_path: string) {
  return { status: "ok" };
}

function mockUpload(_path: string, formData: FormData) {
  const file = formData.get("file") as File | null;
  return {
    id: "tender-004",
    filename: file?.name || "uploaded-document.pdf",
    status: "uploaded",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    page_count: 12,
    file_size: file?.size || 2_400_000,
  } as Tender;
}

export * from './tenders';
export * from './compliance';
export * from './rag';
export * from './responses';
export * from './exports';
export * from './company';
export * from './system';
