"use client";

import { use } from "react";
import { useState, useEffect, useRef } from "react";
import { getRAGHistory, queryRAG, clearRAGHistory } from "@/lib/api/rag";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { formatDateTime } from "@/lib/utils";
import type { RAGMessage } from "@/types";

export default function AskPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [messages, setMessages] = useState<RAGMessage[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [querying, setQuerying] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const history = await getRAGHistory(id);
        setMessages(history);
      } catch (err) {
        console.error("Failed to load chat history:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || querying) return;

    const userQuery = query.trim();
    setQuery("");
    setQuerying(true);

    try {
      const response = await queryRAG(id, userQuery);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          tender_id: id,
          role: "user",
          content: userQuery,
          created_at: new Date().toISOString(),
        },
        {
          id: (Date.now() + 1).toString(),
          tender_id: id,
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          created_at: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      console.error("Failed to query:", err);
    } finally {
      setQuerying(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await clearRAGHistory(id);
      setMessages([]);
    } catch (err) {
      console.error("Failed to clear history:", err);
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
            Ask the Assistant
          </h1>
          <p className="text-[#434655] mt-1">Query the tender document using AI-powered RAG</p>
        </div>
        {messages.length > 0 && (
          <Button variant="ghost" size="sm" onClick={handleClearHistory}>
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Clear History
          </Button>
        )}
      </div>

      <Card className="flex flex-col h-[calc(100vh-280px)]">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-[#EAEDFF] flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-[#004AC6]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="font-headline text-lg font-bold text-[#131B2E] mb-2">Ask about this tender</h3>
              <p className="text-sm text-[#434655] max-w-md">
                Get instant answers to questions about the tender document. The assistant will cite relevant sections from the document.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-gradient-to-r from-[#004AC6] to-[#2563EB] text-white"
                      : "bg-[#EAEDFF] text-[#131B2E]"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p
                    className={`text-xs mt-2 ${
                      message.role === "user" ? "text-white/70" : "text-[#737686]"
                    }`}
                  >
                    {formatDateTime(message.created_at)}
                  </p>
                  {message.sources && message.sources.length > 0 && message.role === "assistant" && (
                    <div className="mt-3 pt-3 border-t border-[#C3C6D7]/30">
                      <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686] mb-2">Sources</p>
                      <div className="space-y-2">
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="text-xs bg-white rounded-lg p-2">
                            <p className="font-semibold text-[#004AC6]">Page {source.page} - {source.section}</p>
                            <p className="text-[#434655] mt-1">{source.excerpt}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {querying && (
            <div className="flex justify-start">
              <div className="bg-[#EAEDFF] rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2">
                  <Spinner size="sm" />
                  <span className="text-sm text-[#434655]">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-[#C3C6D7]/20 p-4">
          <form onSubmit={handleQuery} className="flex gap-3">
            <Textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about this tender..."
              className="flex-1"
              rows={2}
              disabled={querying}
            />
            <Button type="submit" variant="primary" disabled={querying || !query.trim()}>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}