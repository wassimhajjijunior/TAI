import { api } from './client';
import type { CompanyProfile, Annex, PaginatedResponse } from '@/types';

export async function getCompanyProfile(): Promise<CompanyProfile> {
  return api.get<CompanyProfile>('/company/profile');
}

export async function updateCompanyProfile(profile: Partial<CompanyProfile>): Promise<CompanyProfile> {
  return api.put<CompanyProfile>('/company/profile', profile);
}

export async function getAnnexes(params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<Annex>> {
  return api.get<PaginatedResponse<Annex>>('/company/annexes', params);
}

export async function uploadAnnex(formData: FormData): Promise<Annex> {
  return api.upload<Annex>('/company/annexes', formData);
}

export async function deleteAnnex(annexId: string): Promise<void> {
  return api.delete(`/company/annexes/${annexId}`);
}
