import { getTender } from "@/lib/api/tenders";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { formatDate, formatBytes, getStatusLabel } from "@/lib/utils";

export default async function TenderOverviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let tender;
  let error: string | null = null;

  try {
    tender = await getTender(id);
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load tender";
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-[#BA1A1A] py-8">{error}</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!tender) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

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
            <Badge variant={getStatusVariant(tender.status)} size="md">
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
                  <Badge variant={tender.metadata.risk_rating === "high" ? "error" : tender.metadata.risk_rating === "moderate" ? "warning" : "success"} size="sm">
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