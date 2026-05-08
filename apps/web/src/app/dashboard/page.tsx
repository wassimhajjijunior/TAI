import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import type { Tender } from "@/types";

const mockTenders: Tender[] = [
  {
    id: "1",
    filename: "RFP-2024-001_IT_Services.pdf",
    status: "completed",
    created_at: "2024-04-15T10:30:00Z",
    updated_at: "2024-04-15T14:22:00Z",
    page_count: 45,
    file_size: 2500000,
  },
  {
    id: "2", 
    filename: "RFP-2024-002_Facility_Management.pdf",
    status: "qualified",
    created_at: "2024-04-18T09:15:00Z",
    updated_at: "2024-04-19T11:45:00Z",
    page_count: 32,
    file_size: 1800000,
  },
  {
    id: "3",
    filename: "RFP-2024-003_Consulting_Services.pdf",
    status: "reading",
    created_at: "2024-04-20T08:00:00Z",
    updated_at: "2024-04-20T08:05:00Z",
    page_count: 28,
    file_size: 1500000,
  },
  {
    id: "4",
    filename: "EU_Tender_2024_Logistics.pdf",
    status: "failed",
    created_at: "2024-04-10T13:20:00Z",
    updated_at: "2024-04-10T15:30:00Z",
    page_count: 67,
    file_size: 3200000,
  },
  {
    id: "5",
    filename: "Qatar_Airport_Services_2024.pdf",
    status: "generating",
    created_at: "2024-04-21T10:00:00Z",
    updated_at: "2024-04-21T10:15:00Z",
    page_count: 52,
    file_size: 2800000,
  },
];

export default async function DashboardPage() {
  const tenders = mockTenders;
  const healthStatus = "healthy";

  const completedCount = tenders.filter(t => t.status === "completed").length;
  const failedCount = tenders.filter(t => t.status === "failed").length;
  const activeCount = tenders.filter(t => !["completed", "failed"].includes(t.status)).length;

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "completed": return "success";
      case "failed": return "error";
      case "qualified": return "success";
      case "reading": return "info";
      case "indexing": return "info";
      case "qualifying": return "warning";
      case "generating": return "warning";
      default: return "default";
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold font-headline tracking-tight text-[#131B2E]">
          Dashboard
        </h1>
        <p className="text-[#434655] mt-1">Overview of your tender portfolio and system status</p>
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
                <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">Total Tenders</p>
                <p className="text-2xl font-bold text-[#131B2E]">{tenders.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#007D55]/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-[#007D55]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">System Status</p>
                <p className="text-lg font-bold text-[#131B2E]">{healthStatus === "healthy" ? "All Systems Operational" : "Checking..."}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#2563EB]/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-[#2563EB]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">Active Processing</p>
                <p className="text-2xl font-bold text-[#131B2E]">{activeCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="p-6 border-b border-[#C3C6D7]/20">
            <div className="flex justify-between items-center">
              <h2 className="font-headline text-lg font-bold text-[#131B2E]">Recent Tenders</h2>
              <Link href="/dashboard/tenders" className="text-[#004AC6] text-sm font-semibold hover:underline">View All</Link>
            </div>
          </div>
          <div className="p-6 space-y-4">
            {tenders.slice(0, 4).map((tender) => (
              <Link 
                key={tender.id} 
                href={`/dashboard/tenders/${tender.id}/overview`}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-[#F2F3FF] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[#EAEDFF] flex items-center justify-center">
                    <svg className="w-5 h-5 text-[#004AC6]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-bold text-[#131B2E]">{tender.filename}</p>
                    <p className="text-xs text-[#434655]">{tender.page_count || 0} pages</p>
                  </div>
                </div>
                <Badge variant={getStatusVariant(tender.status)}>
                  {tender.status}
                </Badge>
              </Link>
            ))}
          </div>
        </Card>

        <Card>
          <div className="p-6 border-b border-[#C3C6D7]/20">
            <h2 className="font-headline text-lg font-bold text-[#131B2E]">Quick Actions</h2>
          </div>
          <div className="p-6 space-y-4">
            <Link
              href="/dashboard/tenders/new"
              className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-r from-[#004AC6] to-[#2563EB] text-white hover:shadow-lg transition-shadow"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <div>
                <p className="font-bold">Upload New Tender</p>
                <p className="text-sm text-white/80">Upload a tender document for AI analysis</p>
              </div>
            </Link>

            <Link
              href="/dashboard/company/profile"
              className="flex items-center gap-4 p-4 rounded-xl border border-[#C3C6D7]/20 hover:bg-[#F2F3FF] transition-colors"
            >
              <svg className="w-6 h-6 text-[#434655]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H4m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <div>
                <p className="font-bold text-[#131B2E]">Company Profile</p>
                <p className="text-sm text-[#434655]">Update your company information</p>
              </div>
            </Link>

            <Link
              href="/dashboard/company/credentials"
              className="flex items-center gap-4 p-4 rounded-xl border border-[#C3C6D7]/20 hover:bg-[#F2F3FF] transition-colors"
            >
              <svg className="w-6 h-6 text-[#434655]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-bold text-[#131B2E]">Manage Credentials</p>
                <p className="text-sm text-[#434655]">Upload certifications and compliance docs</p>
              </div>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}