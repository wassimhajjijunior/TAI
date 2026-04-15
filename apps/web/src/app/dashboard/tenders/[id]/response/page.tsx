"use client";

import { use } from "react";
import { useState, useEffect } from "react";
import { getDraftResponses, generateDraftResponse, updateDraftResponse, deleteDraftResponse } from "@/lib/api/responses";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { formatDateTime } from "@/lib/utils";
import type { DraftResponse } from "@/types";

export default function ResponsePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [responses, setResponses] = useState<DraftResponse[]>([]);
  const [selectedResponse, setSelectedResponse] = useState<DraftResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");

  useEffect(() => {
    const fetchResponses = async () => {
      try {
        const data = await getDraftResponses(id);
        setResponses(data);
        if (data.length > 0 && !selectedResponse) {
          setSelectedResponse(data[0]);
          setEditContent(data[0].content);
        }
      } catch (err) {
        console.error("Failed to load responses:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchResponses();
  }, [id]);

  useEffect(() => {
    if (selectedResponse) {
      setEditContent(selectedResponse.content);
    }
  }, [selectedResponse]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const newResponse = await generateDraftResponse(id);
      const data = await getDraftResponses(id);
      setResponses(data);
      setSelectedResponse(newResponse);
    } catch (err) {
      console.error("Failed to generate response:", err);
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!selectedResponse) return;
    setSaving(true);
    try {
      await updateDraftResponse(id, selectedResponse.id, editContent);
      const data = await getDraftResponses(id);
      setResponses(data);
      setSelectedResponse((prev) => prev ? { ...prev, content: editContent } : null);
    } catch (err) {
      console.error("Failed to save response:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (responseId: string) => {
    setDeleting(responseId);
    try {
      await deleteDraftResponse(id, responseId);
      const data = await getDraftResponses(id);
      setResponses(data);
      if (selectedResponse?.id === responseId) {
        setSelectedResponse(data.length > 0 ? data[0] : null);
      }
    } catch (err) {
      console.error("Failed to delete response:", err);
    } finally {
      setDeleting(null);
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
            Draft Responses
          </h1>
          <p className="text-[#434655] mt-1">Manage and edit AI-generated tender responses</p>
        </div>
        <Button variant="primary" onClick={handleGenerate} disabled={generating}>
          {generating ? (
            <>
              <Spinner size="sm" className="mr-2" />
              Generating...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Generate New Response
            </>
          )}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card padding="none" className="lg:col-span-1">
          <div className="p-4 border-b border-[#C3C6D7]/20">
            <h2 className="font-headline text-sm font-bold text-[#131B2E]">Saved Drafts</h2>
          </div>
          <div className="divide-y divide-[#C3C6D7]/20 max-h-[500px] overflow-y-auto">
            {responses.length === 0 ? (
              <div className="p-4 text-center text-sm text-[#434655]">
                No drafts yet. Generate a response to get started.
              </div>
            ) : (
              responses.map((response) => (
                <div
                  key={response.id}
                  className={`p-4 cursor-pointer hover:bg-[#F2F3FF] transition-colors ${
                    selectedResponse?.id === response.id ? "bg-[#F2F3FF]" : ""
                  }`}
                  onClick={() => setSelectedResponse(response)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-[#131B2E] truncate">{response.filename}</p>
                      <p className="text-xs text-[#737686]">Version {response.version}</p>
                      <p className="text-xs text-[#737686] mt-1">{formatDateTime(response.updated_at)}</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(response.id);
                      }}
                      className="p-1 text-[#737686] hover:text-[#BA1A1A] transition-colors"
                      disabled={deleting === response.id}
                    >
                      {deleting === response.id ? (
                        <Spinner size="sm" />
                      ) : (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      )}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card className="lg:col-span-2">
          {selectedResponse ? (
            <CardContent className="p-6 space-y-4">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="font-headline text-lg font-bold text-[#131B2E]">{selectedResponse.filename}</h2>
                  <p className="text-sm text-[#737686]">
                    Version {selectedResponse.version} - Last edited {formatDateTime(selectedResponse.updated_at)}
                  </p>
                </div>
                <Button variant="primary" onClick={handleSave} disabled={saving}>
                  {saving ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      Save Changes
                    </>
                  )}
                </Button>
              </div>
              <Textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="min-h-[400px] font-mono text-sm"
                placeholder="Response content will appear here..."
              />
              <p className="text-xs text-[#737686]">
                Edit the response content above. Click Save Changes when finished.
              </p>
            </CardContent>
          ) : (
            <CardContent className="p-6">
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="w-16 h-16 rounded-full bg-[#EAEDFF] flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-[#004AC6]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="font-headline text-lg font-bold text-[#131B2E] mb-2">Select a draft to edit</h3>
                <p className="text-sm text-[#434655] max-w-md">
                  Choose a draft from the list, or generate a new response to get started.
                </p>
              </div>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  );
}