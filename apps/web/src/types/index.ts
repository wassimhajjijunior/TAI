export interface Tender {
  id: string;
  filename: string;
  status: TenderStatus;
  created_at: string;
  updated_at: string;
  page_count?: number;
  file_size?: number;
  metadata?: TenderMetadata;
}

export type TenderStatus = 
  | 'uploaded'
  | 'reading'
  | 'indexing'
  | 'qualifying'
  | 'qualified'
  | 'generating'
  | 'completed'
  | 'failed';

export interface TenderMetadata {
  title?: string;
  authority?: string;
  reference_number?: string;
  submission_date?: string;
  risk_rating?: 'low' | 'moderate' | 'high';
}

export interface ComplianceRequirement {
  id: string;
  tender_id: string;
  clause: string;
  requirement: string;
  status: 'met' | 'unmet' | 'review';
  evidence?: string;
  created_at: string;
}

export interface ComplianceScore {
  id: string;
  eligibility_score: number | null;
  total_requirements: number;
  met_requirements: number;
  recommendation: string | null;
  go_no_go?: 'go' | 'no-go' | 'review';
}

export interface RAGMessage {
  id: string;
  tender_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: RAGSource[];
  created_at: string;
}

export interface RAGSource {
  page: number;
  section: string;
  excerpt: string;
  relevance: number;
}

export interface DraftResponse {
  id: string;
  tender_id: string;
  filename: string;
  content: string;
  version: number;
  created_at: string;
  updated_at: string;
  edited_by?: string;
}

export interface Export {
  id: string;
  tender_id: string;
  type: 'pdf' | 'docx' | 'xlsx';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  filename: string;
  created_at: string;
  download_url?: string;
}

export interface CompanyProfile {
  id: string;
  name: string;
  description?: string;
  website?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  created_at: string;
  updated_at: string;
}

export interface Annex {
  id: string;
  filename: string;
  type: string;
  uploaded_at: string;
  size?: number;
}

export interface ActivityLog {
  id: string;
  tender_id?: string;
  action: string;
  details?: string;
  created_at: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    database: ServiceStatus;
    rabbitmq: ServiceStatus;
    redis: ServiceStatus;
  };
  checked_at: string;
}

export interface ServiceStatus {
  status: 'up' | 'down';
  latency_ms?: number;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit?: number;
  offset?: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
}

export interface APIError {
  detail: string;
  status_code: number;
}
