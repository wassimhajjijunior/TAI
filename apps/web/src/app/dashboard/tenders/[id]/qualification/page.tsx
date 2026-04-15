"use client";

import { use } from "react";
import { useState, useEffect } from "react";
import { getComplianceRequirements, getComplianceScore, updateRequirementStatus, runQualificationCheck } from "@/lib/api/compliance";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { ComplianceRequirement, ComplianceScore } from "@/types";

export default function QualificationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [requirements, setRequirements] = useState<ComplianceRequirement[]>([]);
  const [score, setScore] = useState<ComplianceScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningCheck, setRunningCheck] = useState(false);
  const [updating, setUpdating] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [reqs, complianceScore] = await Promise.all([
          getComplianceRequirements(id),
          getComplianceScore(id),
        ]);
        setRequirements(reqs);
        setScore(complianceScore);
      } catch (err) {
        console.error("Failed to load compliance data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleRunCheck = async () => {
    setRunningCheck(true);
    try {
      await runQualificationCheck(id);
      const [reqs, complianceScore] = await Promise.all([
        getComplianceRequirements(id),
        getComplianceScore(id),
      ]);
      setRequirements(reqs);
      setScore(complianceScore);
    } catch (err) {
      console.error("Failed to run qualification check:", err);
    } finally {
      setRunningCheck(false);
    }
  };

  const handleStatusUpdate = async (requirementId: string, status: "met" | "unmet" | "review") => {
    setUpdating(requirementId);
    try {
      await updateRequirementStatus(id, requirementId, status);
      setRequirements((prev) =>
        prev.map((req) => (req.id === requirementId ? { ...req, status } : req))
      );
      const complianceScore = await getComplianceScore(id);
      setScore(complianceScore);
    } catch (err) {
      console.error("Failed to update requirement status:", err);
    } finally {
      setUpdating(null);
    }
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

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

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
              <Badge variant={score.go_no_go === "go" ? "success" : score.go_no_go === "no-go" ? "error" : "warning"} size="md">
                {score.go_no_go === "go" ? "GO" : score.go_no_go === "no-go" ? "NO-GO" : "REVIEW"}
              </Badge>
              <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mt-1">Recommendation</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Card padding="none">
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
                      <Badge variant={getStatusVariant(req.status)} size="sm">
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