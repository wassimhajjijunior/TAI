"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export default function NewTenderPage() {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mockUpload = useCallback(async (file: File) => {
    setError(null);
    setUploading(true);
    setUploadProgress(0);

    const totalSteps = 10;
    for (let i = 1; i <= totalSteps; i++) {
      await new Promise(resolve => setTimeout(resolve, 300));
      setUploadProgress((i / totalSteps) * 100);
    }

    const mockId = Date.now().toString();
    router.push(`/dashboard/tenders/${mockId}/overview`);
  }, [router]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === "application/pdf") {
      mockUpload(file);
    } else {
      setError("Please upload a PDF file");
    }
  }, [mockUpload]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      mockUpload(file);
    }
  }, [mockUpload]);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold font-headline tracking-tight text-[#131B2E]">
          Upload New Tender
        </h1>
        <p className="text-[#434655] mt-1">Upload a tender document to start the analysis process</p>
      </div>

      <Card>
        <CardContent className="p-8">
          <div
            className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
              dragActive
                ? "border-[#004AC6] bg-[#F2F3FF]"
                : "border-[#C3C6D7]/40 hover:border-[#004AC6]/50"
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
          >
            <div className="w-16 h-16 rounded-full bg-[#EAEDFF] flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-[#004AC6]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="font-headline text-lg font-bold text-[#131B2E] mb-2">
              Drag and drop your tender here
            </h3>
            <p className="text-sm text-[#434655] mb-4">or click to browse</p>
            <label className="cursor-pointer inline-block">
              <input type="file" accept=".pdf" className="hidden" onChange={handleFileChange} disabled={uploading} />
              <Button variant="primary" disabled={uploading}>
                {uploading ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Processing...
                  </>
                ) : (
                  "Select PDF File"
                )}
              </Button>
            </label>
            <p className="text-xs text-[#737686] mt-4">Supports PDF files up to 50MB</p>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-[#FFDAD6] text-[#BA1A1A] rounded-xl text-sm">
              {error}
            </div>
          )}

          {uploading && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-[#131B2E]">Uploading document...</span>
                <span className="text-sm text-[#737686]">{Math.round(uploadProgress)}%</span>
              </div>
              <div className="h-2 bg-[#EAEDFF] rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-[#004AC6] to-[#2563EB] rounded-full transition-all duration-300" 
                  style={{ width: `${uploadProgress}%` }} 
                />
              </div>
              <p className="text-xs text-[#737686] mt-2">This may take a few moments depending on file size</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h3 className="font-headline text-lg font-bold text-[#131B2E] mb-4">What happens next?</h3>
          <ul className="space-y-3">
            {[
              { step: "1", title: "Document Upload", desc: "Your tender PDF is securely uploaded to our processing pipeline" },
              { step: "2", title: "AI Analysis", desc: "Our AI reads and indexes the document for search and qualification checks" },
              { step: "3", title: "Qualification Review", desc: "System checks compliance requirements and highlights areas needing attention" },
              { step: "4", title: "Response Generation", desc: "AI generates draft responses based on your company profile and credentials" },
            ].map((item) => (
              <li key={item.step} className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-[#004AC6] text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                  {item.step}
                </div>
                <div>
                  <p className="font-semibold text-[#131B2E]">{item.title}</p>
                  <p className="text-sm text-[#434655]">{item.desc}</p>
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}