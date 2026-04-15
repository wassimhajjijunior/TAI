import { api } from './client';
import type { Export, PaginatedResponse } from '@/types';

export interface ExportsListParams {
  page?: number;
  page_size?: number;
}

export async function getExports(tenderId: string, params?: ExportsListParams): Promise<PaginatedResponse<Export>> {
  return api.get<PaginatedResponse<Export>>(`/documents/${tenderId}/exports`, params as Record<string, string | number | undefined>);
}

export async function createExport(tenderId: string, type: 'pdf' | 'docx' | 'xlsx'): Promise<Export> {
  return api.post<Export>(`/documents/${tenderId}/export`, { type });
}

export async function getExport(tenderId: string, exportId: string): Promise<Export> {
  return api.get<Export>(`/exports/${exportId}`);
}

export async function deleteExport(tenderId: string, exportId: string): Promise<void> {
  return api.delete(`/exports/${exportId}`);
}

import { getApiBaseUrl } from "@/lib/utils";

export function getExportDownloadUrl(exportId: string): string {
  return `${getApiBaseUrl()}/exports/${exportId}/download`;
}
