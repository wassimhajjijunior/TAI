"use client";

import { useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/ui/states";
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
  {
    id: "6",
    filename: "Singapore_HDB_Construction_2024.pdf",
    status: "indexing",
    created_at: "2024-04-22T08:00:00Z",
    updated_at: "2024-04-22T08:10:00Z",
    page_count: 89,
    file_size: 4500000,
  },
  {
    id: "7",
    filename: "Dubai_Metro_Phase_4_Tender.pdf",
    status: "qualified",
    created_at: "2024-04-19T14:30:00Z",
    updated_at: "2024-04-20T09:00:00Z",
    page_count: 156,
    file_size: 7800000,
  },
];

export default function TendersPage() {
  const [tenders, setTenders] = useState<Tender[]>(mockTenders);
  const [loading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    setUploading(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setUploading(false);
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "error";
      case "qualified":
        return "success";
      default:
        return "info";
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold font-headline tracking-tight text-[#131B2E]">
            Tender Library
          </h1>
          <p className="text-[#434655] mt-1">Manage and track all your tender documents</p>
        </div>
        <label className="cursor-pointer">
          <input type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={handleUpload} disabled={uploading} />
          <Button variant="primary" disabled={uploading}>
            {uploading ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Uploading...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Upload Tender
              </>
            )}
          </Button>
        </label>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : tenders.length === 0 ? (
        <EmptyState
          title="No tenders yet"
          description="Upload your first tender document to get started with AI-powered analysis and response generation."
          action={
            <label className="cursor-pointer">
              <input type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={handleUpload} />
              <Button variant="primary">Upload Your First Tender</Button>
            </label>
          }
        />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#C3C6D7]/20">
                  <th className="text-left p-4 text-[10px] uppercase tracking-wider font-bold text-[#737686]">Filename</th>
                  <th className="text-left p-4 text-[10px] uppercase tracking-wider font-bold text-[#737686]">Status</th>
                  <th className="text-left p-4 text-[10px] uppercase tracking-wider font-bold text-[#737686]">Pages</th>
                  <th className="text-left p-4 text-[10px] uppercase tracking-wider font-bold text-[#737686]">Size</th>
                  <th className="text-left p-4 text-[10px] uppercase tracking-wider font-bold text-[#737686]">Created</th>
                  <th className="text-right p-4 text-[10px] uppercase tracking-wider font-bold text-[#737686]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#C3C6D7]/20">
                {tenders.map((tender) => (
                  <tr key={tender.id} className="hover:bg-[#F2F3FF] transition-colors">
                    <td className="p-4">
                      <Link href={`/dashboard/tenders/${tender.id}/overview`} className="font-medium text-[#131B2E] hover:text-[#004AC6]">
                        {tender.filename}
                      </Link>
                    </td>
                    <td className="p-4">
                      <Badge variant={getStatusVariant(tender.status)}>
                        {tender.status}
                      </Badge>
                    </td>
                    <td className="p-4 text-sm text-[#434655]">{tender.page_count || "-"}</td>
                    <td className="p-4 text-sm text-[#434655]">{formatSize(tender.file_size || 0)}</td>
                    <td className="p-4 text-sm text-[#434655]">
                      {new Date(tender.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-4 text-right">
                      <Link href={`/dashboard/tenders/${tender.id}/overview`}>
                        <Button variant="ghost" size="sm">View</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}