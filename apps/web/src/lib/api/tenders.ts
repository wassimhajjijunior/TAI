import { api } from './client';
import type { Tender, PaginatedResponse } from '@/types';

export interface TendersListParams {
  page?: number;
  page_size?: number;
  status?: string;
  search?: string;
}

export async function getTenders(params?: TendersListParams): Promise<PaginatedResponse<Tender>> {
  const response = await api.get<{ items: Tender[] }>('/documents', params as Record<string, string | number | undefined>);
  const items = response.items ?? [];
  return {
    items,
    total: items.length,
    page: params?.page ?? 1,
    page_size: params?.page_size ?? items.length,
  };
}

export async function getTender(id: string): Promise<Tender> {
  const response = await api.get<{ document: Tender }>(`/documents/${id}`);
  return response.document;
}

export async function uploadTender(formData: FormData): Promise<Tender> {
  return api.upload<Tender>('/documents', formData);
}

export async function deleteTender(id: string): Promise<void> {
  return api.delete(`/documents/${id}`);
}
