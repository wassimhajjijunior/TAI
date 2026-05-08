"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { ComplianceRequirement, ComplianceScore } from "@/types";

const mockRequirements: ComplianceRequirement[] = [
  {
    id: "1",
    tender_id: "1",
    clause: "4.1.1",
    requirement: "Company must be registered for minimum 3 years",
    status: "met",
    evidence: "Business registration certificate dated 2021",
    created_at: "2024-04-15T10:30:00Z",
  },
  {
    id: "2",
    tender_id: "1",
    clause: "4.2.3",
    requirement: "Annual turnover must exceed $5 million",
    status: "met",
    evidence: "Audited financial statements 2022-2023",
    created_at: "2024-04-15T10:30:00Z",
  },
  {
    id: "3",
    tender_id: "1",
    clause: "5.1.2",
    requirement: "ISO 27001 certification required",
    status: "met",
    evidence: "Certificate valid until 2026",
    created_at: "2024-04-15T10:30:00Z",
  },
  {
    id: "4",
    tender_id: "1",
    clause: "6.3.1",
    requirement: "Local presence in target country",
    status: "review",
    evidence: "Office lease agreement under review",
    created_at: "2024-04-15T10:30:00Z",
  },
  {
    id: "5",
    tender_id: "1",
    clause: "7.2.4",
    requirement: "Previous experience with similar projects",
    status: "met",
    evidence: "3 completed projects in last 2 years",
    created_at: "2024-04-15T10:30:00Z",
  },
  {
    id: "6",
    tender_id: "1",
    clause: "8.1.1",
    requirement: "Professional indemnity insurance $10M",
    status: "unmet",
    evidence: "Current coverage $2M - needs upgrade",
    created_at: "2024-04-15T10:30:00Z",
  },
];

const mockScore: ComplianceScore = {
  id: "1",
  eligibility_score: 83.3,
  total_requirements: 6,
  met_requirements: 4,
  recommendation: "Meets 83% of compliance requirements",
  go_no_go: "go",
};

export default function QualificationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const [requirements] = useState<ComplianceRequirement[]>(mockRequirements);
  const [score] = useState<ComplianceScore>(mockScore);
  const [runningCheck, setRunningCheck] = useState(false);
  const [updating, setUpdating] = useState<string | null>(null);

  const handleRunCheck = async () => {
    setRunningCheck(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setRunningCheck(false);
  };

  const handleStatusUpdate = async (requirementId: string, status: "met" | "unmet" | "review") => {
    setUpdating(requirementId);
    await new Promise((resolve) => setTimeout(resolve, 500));
    setUpdating(null);
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "met":
        return "success";
      case "unmet":
        return "error";
      case "review":
        return "warning";
      default:
        return "default";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold font-headline tracking-tight text-[#131B2E]">
            Compliance Qualification
          </h1>
          <p className="text-[#434655] mt-1">Review and manage compliance requirements</p>
        </div>
        <Button variant="primary" onClick={handleRunCheck} disabled={runningCheck}>
          {runningCheck ? (
            <>
              <Spinner size="sm" className="mr-2" />
              Running Check...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Re-run Qualification Check
            </>
          )}
        </Button>
      </div>

      {score && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-[#131B2E]">{score.eligibility_score != null ? Math.round(score.eligibility_score) : "—"}%</p>
              <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mt-1">Compliance Score</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-[#007D55]">{score.met_requirements}</p>
              <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mt-1">Requirements Met</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-[#BA1A1A]">{score.total_requirements - score.met_requirements}</p>
              <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mt-1">Unmet</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Badge variant={score.go_no_go === "go" ? "success" : score.go_no_go === "no-go" ? "error" : "warning"}>
                {score.go_no_go === "go" ? "GO" : score.go_no_go === "no-go" ? "NO-GO" : "REVIEW"}
              </Badge>
              <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mt-1">Recommendation</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <div className="p-6 border-b border-[#C3C6D7]/20">
          <h2 className="font-headline text-lg font-bold text-[#131B2E]">Requirements Checklist</h2>
        </div>
        <div className="divide-y divide-[#C3C6D7]/20">
          {requirements.length === 0 ? (
            <div className="p-6 text-center text-[#434655]">
              No compliance requirements found. Run a qualification check to analyze the tender.
            </div>
          ) : (
            requirements.map((req) => (
              <div key={req.id} className="p-4 hover:bg-[#F2F3FF] transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={getStatusVariant(req.status)}>
                        {req.status}
                      </Badge>
                    </div>
                    <p className="text-sm font-semibold text-[#131B2E] mb-1">{req.clause}</p>
                    <p className="text-sm text-[#434655]">{req.requirement}</p>
                    {req.evidence && (
                      <p className="text-xs text-[#737686] mt-2 italic">Evidence: {req.evidence}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant={req.status === "met" ? "primary" : "secondary"}
                      size="sm"
                      onClick={() => handleStatusUpdate(req.id, "met")}
                      disabled={updating === req.id}
                    >
                      Met
                    </Button>
                    <Button
                      variant={req.status === "unmet" ? "destructive" : "ghost"}
                      size="sm"
                      onClick={() => handleStatusUpdate(req.id, "unmet")}
                      disabled={updating === req.id}
                    >
                      Unmet
                    </Button>
                    <Button
                      variant={req.status === "review" ? "secondary" : "ghost"}
                      size="sm"
                      onClick={() => handleStatusUpdate(req.id, "review")}
                      disabled={updating === req.id}
                    >
                      Review
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
