import { api } from './client';
import type { ComplianceRequirement, ComplianceScore } from '@/types';

export async function getComplianceRequirements(tenderId: string): Promise<ComplianceRequirement[]> {
  return api.get<ComplianceRequirement[]>(`/documents/${tenderId}/compliance`);
}

export async function getComplianceScore(tenderId: string): Promise<ComplianceScore> {
  return api.get<ComplianceScore>(`/documents/${tenderId}/compliance/score`);
}

export async function updateRequirementStatus(
  tenderId: string,
  requirementId: string,
  status: 'met' | 'unmet' | 'review',
  evidence?: string
): Promise<ComplianceRequirement> {
  return api.put<ComplianceRequirement>(
    `/documents/${tenderId}/compliance/${requirementId}`,
    { status, evidence }
  );
}

export async function runQualificationCheck(tenderId: string): Promise<void> {
  return api.post(`/documents/${tenderId}/compliance/check`);
}
