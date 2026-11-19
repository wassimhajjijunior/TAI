import { api } from './client';
import type { RAGMessage, RAGSource } from '@/types';

export interface RAGQueryParams {
  query: string;
  top_k?: number;
}

export interface RAGQueryResponse {
  answer: string;
  sources: RAGSource[];
}

export async function getRAGHistory(tenderId: string): Promise<RAGMessage[]> {
  const response = await api.get<{ messages: RAGMessage[] }>(`/documents/${tenderId}/rag/history`);
  return response.messages ?? [];
}

export async function queryRAG(tenderId: string, query: string): Promise<RAGQueryResponse> {
  return api.post<RAGQueryResponse>(`/rag/query`, { query, document_id: tenderId });
}

export async function clearRAGHistory(tenderId: string): Promise<void> {
  return api.delete(`/documents/${tenderId}/rag/history`);
}
