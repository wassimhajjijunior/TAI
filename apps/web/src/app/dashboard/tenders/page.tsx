"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getTenders, uploadTender } from "@/lib/api/tenders";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/ui/states";
import type { Tender, PaginatedResponse } from "@/types";

interface TendersListResponse extends PaginatedResponse<Tender> {}

export default function TendersPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; status?: string; search?: string }>;
}) {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [sp, setSp] = useState<{ page?: string; status?: string; search?: string }>({});

  useEffect(() => {
    searchParams.then(setSp);
  }, [searchParams]);

  useEffect(() => {
    const fetchTenders = async () => {
      setLoading(true);
      setError(null);
      try {
        const page = sp.page ? parseInt(sp.page, 10) : 1;
        const response = await getTenders({
          page,
          page_size: 10,
          status: sp.status,
          search: sp.search,
        });
        setTenders(response.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load tenders");
      } finally {
        setLoading(false);
      }
    };

    fetchTenders();
  }, [sp.page, sp.status, sp.search]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    try {
      await uploadTender(formData);
      const response = await getTenders({ page: 1, page_size: 10 });
      setTenders(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload tender");
    } finally {
      setUploading(false);
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "error";
      default:
        return "info";
    }
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
      ) : error ? (
        <Card>
          <div className="p-6 text-center text-[#BA1A1A]">{error}</div>
        </Card>
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
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#C3C6D7]/20">
                  <th className="text-left p-4 text-[10px] uppercase tracking-wider font-bold text-[#737686]">Filename</th>
                  <th className="text-left p-4 text-[10px] uppercase tracking-wider font-bold text-[#737686]">Status</th>
                  <th className="text-left p-4 text-[10px] uppercase tracking-wider font-bold text-[#737686]">Pages</th>
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
                      <Badge variant={getStatusVariant(tender.status)} size="sm">
                        {tender.status}
                      </Badge>
                    </td>
                    <td className="p-4 text-sm text-[#434655]">{tender.page_count || "-"}</td>
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