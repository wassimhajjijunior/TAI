import { api } from './client';
import type { DraftResponse } from '@/types';

interface ResponseRecordDTO {
  id: string;
  document_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

function toDraftResponse(item: ResponseRecordDTO): DraftResponse {
  return {
    id: item.id,
    tender_id: item.document_id,
    filename: `Response_${item.id.slice(0, 8)}.docx`,
    content: item.content,
    version: 1,
    created_at: item.created_at,
    updated_at: item.updated_at,
  };
}

export async function getDraftResponses(tenderId: string): Promise<DraftResponse[]> {
  const response = await api.get<{ responses: ResponseRecordDTO[] }>(`/documents/${tenderId}/responses`);
  return (response.responses ?? []).map(toDraftResponse);
}

export async function getDraftResponse(tenderId: string, responseId: string): Promise<DraftResponse> {
  return api.get<DraftResponse>(`/documents/${tenderId}/responses/${responseId}`);
}

export async function generateDraftResponse(tenderId: string): Promise<DraftResponse> {
  return api.post<DraftResponse>(`/documents/${tenderId}/responses/generate`);
}

export async function updateDraftResponse(
  tenderId: string,
  responseId: string,
  content: string
): Promise<DraftResponse> {
  return api.put<DraftResponse>(
    `/documents/${tenderId}/responses/${responseId}`,
    { content }
  );
}

export async function deleteDraftResponse(tenderId: string, responseId: string): Promise<void> {
  return api.delete(`/documents/${tenderId}/responses/${responseId}`);
}
