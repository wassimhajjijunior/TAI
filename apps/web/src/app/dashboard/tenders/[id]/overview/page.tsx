import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate, formatBytes, getStatusLabel } from "@/lib/utils";
import type { Tender } from "@/types";

const mockTenders: Record<string, Tender> = {
  "1": {
    id: "1",
    filename: "RFP-2024-001_IT_Services.pdf",
    status: "completed",
    created_at: "2024-04-15T10:30:00Z",
    updated_at: "2024-04-15T14:22:00Z",
    page_count: 45,
    file_size: 2500000,
    metadata: {
      title: "IT Infrastructure & Managed Services Tender",
      authority: "Ministry of Digital Transformation",
      reference_number: "RFP-2024-001-MDT",
      submission_date: "2024-05-30T23:59:00Z",
      risk_rating: "moderate",
    },
  },
  "2": {
    id: "2",
    filename: "RFP-2024-002_Facility_Management.pdf",
    status: "qualified",
    created_at: "2024-04-18T09:15:00Z",
    updated_at: "2024-04-19T11:45:00Z",
    page_count: 32,
    file_size: 1800000,
    metadata: {
      title: "Facility Management & Maintenance Services",
      authority: "National Housing Authority",
      reference_number: "RFP-2024-002-NHA",
      submission_date: "2024-06-15T23:59:00Z",
      risk_rating: "low",
    },
  },
  "3": {
    id: "3",
    filename: "RFP-2024-003_Consulting_Services.pdf",
    status: "reading",
    created_at: "2024-04-20T08:00:00Z",
    updated_at: "2024-04-20T08:05:00Z",
    page_count: 28,
    file_size: 1500000,
  },
  "4": {
    id: "4",
    filename: "EU_Tender_2024_Logistics.pdf",
    status: "failed",
    created_at: "2024-04-10T13:20:00Z",
    updated_at: "2024-04-10T15:30:00Z",
    page_count: 67,
    file_size: 3200000,
    metadata: {
      title: "EU Logistics & Supply Chain Management",
      authority: "European Commission - DG MOVE",
      reference_number: "EU-2024-LOG-042",
      submission_date: "2024-04-25T17:00:00Z",
      risk_rating: "high",
    },
  },
  "5": {
    id: "5",
    filename: "Qatar_Airport_Services_2024.pdf",
    status: "generating",
    created_at: "2024-04-21T10:00:00Z",
    updated_at: "2024-04-21T10:15:00Z",
    page_count: 52,
    file_size: 2800000,
    metadata: {
      title: "Hamad International Airport - Ground Handling Services",
      authority: "Qatar Civil Aviation Authority",
      reference_number: "QCAA-2024-GH-018",
      submission_date: "2024-07-01T23:59:00Z",
      risk_rating: "moderate",
    },
  },
  "6": {
    id: "6",
    filename: "Singapore_HDB_Construction_2024.pdf",
    status: "indexing",
    created_at: "2024-04-22T08:00:00Z",
    updated_at: "2024-04-22T08:10:00Z",
    page_count: 89,
    file_size: 4500000,
    metadata: {
      title: "HDB Residential Construction Project - Phase 12",
      authority: "Housing & Development Board Singapore",
      reference_number: "HDB-2024-CON-089",
      submission_date: "2024-08-30T17:00:00Z",
      risk_rating: "low",
    },
  },
  "7": {
    id: "7",
    filename: "Dubai_Metro_Phase_4_Tender.pdf",
    status: "qualified",
    created_at: "2024-04-19T14:30:00Z",
    updated_at: "2024-04-20T09:00:00Z",
    page_count: 156,
    file_size: 7800000,
    metadata: {
      title: "Dubai Metro Phase 4 - Rail Extension & Station Works",
      authority: "Dubai Roads & Transport Authority",
      reference_number: "RTA-2024-METRO-P4",
      submission_date: "2024-09-15T23:59:00Z",
      risk_rating: "high",
    },
  },
};

function createNewTender(id: string): Tender {
  const timestamp = parseInt(id) || Date.now();
  return {
    id,
    filename: `New_Tender_${timestamp}.pdf`,
    status: "completed",
    created_at: new Date(timestamp).toISOString(),
    updated_at: new Date(timestamp + 3600000).toISOString(),
    page_count: Math.floor(Math.random() * 50) + 20,
    file_size: Math.floor(Math.random() * 3000000) + 500000,
    metadata: {
      title: "Newly Uploaded Tender Document",
      authority: "Demo Authority",
      reference_number: `DEMO-${timestamp}`,
      submission_date: new Date(timestamp + 30 * 24 * 60 * 60 * 1000).toISOString(),
      risk_rating: "low",
    },
  };
}

export default async function TenderOverviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const tender = mockTenders[id] || createNewTender(id);

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "error";
      case "qualifying":
      case "generating":
        return "warning";
      default:
        return "info";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-extrabold font-headline tracking-tight text-[#131B2E]">
            {tender.filename}
          </h1>
          <div className="flex items-center gap-4 mt-2">
            <Badge variant={getStatusVariant(tender.status)}>
              {getStatusLabel(tender.status)}
            </Badge>
            <span className="text-sm text-[#737686]">
              Uploaded {formatDate(tender.created_at)}
            </span>
          </div>
        </div>
        {tender.status === "completed" && (
          <div className="flex gap-3">
            <Button variant="secondary" size="sm">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit Response
            </Button>
            <Button variant="primary" size="sm">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#004AC6]/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-[#004AC6]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">Pages</p>
                <p className="text-2xl font-bold text-[#131B2E]">{tender.page_count || "-"}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#007D55]/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-[#007D55]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7M4 7l8 5 8-5M4 7l8-5 8 5" />
                </svg>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">File Size</p>
                <p className="text-2xl font-bold text-[#131B2E]">{tender.file_size ? formatBytes(tender.file_size) : "-"}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#B45309]/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-[#B45309]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">Last Updated</p>
                <p className="text-lg font-bold text-[#131B2E]">{formatDate(tender.updated_at)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {tender.metadata && (
        <Card>
          <CardContent>
            <h2 className="font-headline text-lg font-bold text-[#131B2E] mb-4">Document Metadata</h2>
            <div className="grid grid-cols-2 gap-4">
              {tender.metadata.title && (
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mb-1">Title</p>
                  <p className="text-sm text-[#131B2E]">{tender.metadata.title}</p>
                </div>
              )}
              {tender.metadata.authority && (
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mb-1">Issuing Authority</p>
                  <p className="text-sm text-[#131B2E]">{tender.metadata.authority}</p>
                </div>
              )}
              {tender.metadata.reference_number && (
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mb-1">Reference Number</p>
                  <p className="text-sm text-[#131B2E]">{tender.metadata.reference_number}</p>
                </div>
              )}
              {tender.metadata.submission_date && (
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mb-1">Submission Deadline</p>
                  <p className="text-sm text-[#131B2E]">{formatDate(tender.metadata.submission_date)}</p>
                </div>
              )}
              {tender.metadata.risk_rating && (
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mb-1">Risk Rating</p>
                  <Badge variant={tender.metadata.risk_rating === "high" ? "error" : tender.metadata.risk_rating === "moderate" ? "warning" : "success"}>
                    {tender.metadata.risk_rating.toUpperCase()}
                  </Badge>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {tender.status !== "completed" && tender.status !== "failed" && (
        <Card>
          <CardContent>
            <h2 className="font-headline text-lg font-bold text-[#131B2E] mb-4">Processing Status</h2>
            <div className="space-y-4">
              {["uploaded", "reading", "indexing", "qualifying", "qualified", "generating"].map((stage, index) => {
                const stageIndex = ["uploaded", "reading", "indexing", "qualifying", "qualified", "generating"].indexOf(tender.status);
                const isComplete = index < stageIndex;
                const isCurrent = stage === tender.status;

                return (
                  <div key={stage} className="flex items-center gap-4">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isComplete ? "bg-[#007D55] text-white" :
                      isCurrent ? "bg-[#004AC6] text-white animate-pulse" :
                      "bg-[#EAEDFF] text-[#737686]"
                    }`}>
                      {isComplete ? (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <span className="text-xs font-bold">{index + 1}</span>
                      )}
                    </div>
                    <div className="flex-1">
                      <p className={`text-sm font-semibold ${isCurrent ? "text-[#004AC6]" : "text-[#131B2E]"}`}>
                        {getStatusLabel(stage)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
