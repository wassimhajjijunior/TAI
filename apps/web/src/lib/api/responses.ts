import { api } from './client';
import type { DraftResponse } from '@/types';

export async function getDraftResponses(tenderId: string): Promise<DraftResponse[]> {
  return api.get<DraftResponse[]>(`/documents/${tenderId}/responses`);
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
