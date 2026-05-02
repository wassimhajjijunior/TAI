import { api } from './client';
import type { SystemHealth, ActivityLog, PaginatedResponse } from '@/types';

export async function getSystemHealth(): Promise<SystemHealth> {
  return api.get<SystemHealth>('/system/health');
}

export async function getActivityLogs(params?: {
  page?: number;
  page_size?: number;
  tender_id?: string;
}): Promise<PaginatedResponse<ActivityLog>> {
  return api.get<PaginatedResponse<ActivityLog>>('/system/activity', params);
}

export async function getMessagingTopology(): Promise<{
  queues: Array<{ name: string; messages: number; consumers: number }>;
  exchanges: Array<{ name: string; type: string }>;
}> {
  return api.get('/system/messaging/topology');
}
