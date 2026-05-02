"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";

interface Credential {
  id: string;
  name: string;
  description: string;
  expiry_date?: string;
  status: "valid" | "expiring" | "expired";
}

const mockCredentials: Credential[] = [
  { id: "1", name: "ISO 9001:2015", description: "Quality Management System Certification", expiry_date: "2026-06-15", status: "valid" },
  { id: "2", name: "ISO 27001", description: "Information Security Management", expiry_date: "2025-12-01", status: "expiring" },
  { id: "3", name: "Business License", description: "General Business Operation License", expiry_date: "2026-03-20", status: "valid" },
  { id: "4", name: "Tax Clearance", description: "Tax Compliance Certificate", expiry_date: "2024-01-15", status: "expired" },
  { id: "5", name: "Industry Certifications", description: "Sector-specific professional certifications", status: "valid" },
];

export default function CredentialsPage() {
  const [credentials] = useState<Credential[]>(mockCredentials);
  const [uploading, setUploading] = useState(false);

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "valid":
        return "success";
      case "expiring":
        return "warning";
      case "expired":
        return "error";
      default:
        return "default";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "valid":
        return "Valid";
      case "expiring":
        return "Expiring Soon";
      case "expired":
        return "Expired";
      default:
        return status;
    }
  };

  const handleUpload = async () => {
    setUploading(true);
    // Simulate upload
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setUploading(false);
  };

  const validCount = credentials.filter((c) => c.status === "valid").length;
  const expiringCount = credentials.filter((c) => c.status === "expiring").length;
  const expiredCount = credentials.filter((c) => c.status === "expired").length;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold font-headline tracking-tight text-[#131B2E]">
            Credentials
          </h1>
          <p className="text-[#434655] mt-1">Manage your company certifications and compliance documents</p>
        </div>
        <label className="cursor-pointer">
          <input type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={() => handleUpload()} disabled={uploading} />
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
                Add Credential
              </>
            )}
          </Button>
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-[#007D55]">{validCount}</p>
            <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mt-1">Valid Credentials</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-[#B45309]">{expiringCount}</p>
            <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mt-1">Expiring Soon</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-[#BA1A1A]">{expiredCount}</p>
            <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mt-1">Expired</p>
          </CardContent>
        </Card>
      </div>

      <Card padding="none">
        <div className="p-6 border-b border-[#C3C6D7]/20">
          <h2 className="font-headline text-lg font-bold text-[#131B2E]">Your Credentials</h2>
        </div>
        <div className="divide-y divide-[#C3C6D7]/20">
          {credentials.length === 0 ? (
            <div className="p-6 text-center text-[#434655]">
              No credentials uploaded yet. Add your first credential to get started.
            </div>
          ) : (
            credentials.map((credential) => (
              <div key={credential.id} className="p-4 flex items-center justify-between hover:bg-[#F2F3FF] transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-[#EAEDFF] flex items-center justify-center text-[#004AC6]">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.829 2M9 14a3.978 3.978 0 01-.99-2.605V11a2 2 0 012-2h.01" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#131B2E]">{credential.name}</p>
                    <p className="text-xs text-[#434655]">{credential.description}</p>
                    {credential.expiry_date && (
                      <p className="text-xs text-[#737686] mt-1">
                        Expires: {new Date(credential.expiry_date).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={getStatusVariant(credential.status)} size="sm">
                    {getStatusLabel(credential.status)}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h2 className="font-headline text-lg font-bold text-[#131B2E] mb-4">Credential Tips</h2>
          <ul className="space-y-3">
            {[
              "Upload all relevant certifications to improve your tender qualification rate",
              "Set reminders for credentials expiring within 90 days",
              "Ensure all uploaded documents are legible and up-to-date",
              "Include both primary and supporting credentials for comprehensive coverage",
            ].map((item, index) => (
              <li key={index} className="flex items-start gap-3 text-sm text-[#434655]">
                <svg className="w-5 h-5 text-[#004AC6] flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {item}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}