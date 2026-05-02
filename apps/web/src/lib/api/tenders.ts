import { api } from './client';
import type { Tender, PaginatedResponse } from '@/types';

export interface TendersListParams {
  page?: number;
  page_size?: number;
  status?: string;
  search?: string;
}

export async function getTenders(params?: TendersListParams): Promise<PaginatedResponse<Tender>> {
  return api.get<PaginatedResponse<Tender>>('/documents', params as Record<string, string | number | undefined>);
}

export async function getTender(id: string): Promise<Tender> {
  return api.get<Tender>(`/documents/${id}`);
}

export async function uploadTender(formData: FormData): Promise<Tender> {
  return api.upload<Tender>('/documents', formData);
}

export async function deleteTender(id: string): Promise<void> {
  return api.delete(`/documents/${id}`);
}
