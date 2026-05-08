"use client";

import { use } from "react";
import { useState, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { formatDateTime } from "@/lib/utils";
import type { RAGMessage } from "@/types";

const presetQuestions = [
  "What is the submission deadline for this tender?",
  "What are the minimum technical qualifications required?",
];

const getAnswer = (question: string): { content: string; sources?: RAGMessage["sources"] } => {
  const q = question.toLowerCase();
  
  if (q.includes("deadline") || q.includes("submission")) {
    return {
      content: "The submission deadline is May 30, 2024 at 23:59 hours (UTC+3). Late submissions will not be accepted under any circumstances. It is recommended to submit at least 24 hours before the deadline to avoid any technical issues.",
      sources: [
        { page: 2, section: "1.1", excerpt: "Submission Deadline: 30 May 2024, 23:59 UTC+3. Late submissions will not be accepted.", relevance: 0.95 },
        { page: 15, section: "Appendix A", excerpt: "Recommended submission timeline to avoid technical issues.", relevance: 0.78 },
      ],
    };
  }
  
  if (q.includes("qualification") || q.includes("technical")) {
    return {
      content: "The tender requires the following minimum technical qualifications:\n\n1. ISO 27001 certification (mandatory)\n2. Minimum 3 years of relevant industry experience\n3. Annual turnover exceeding $5 million\n4. At least 3 completed projects of similar scope in the last 5 years\n5. Local presence or partnership with local entity\n\nDetailed requirements are outlined in Section 4 of the tender document.",
      sources: [
        { page: 5, section: "4.1", excerpt: "ISO 27001 certification is mandatory for all bidders.", relevance: 0.98 },
        { page: 5, section: "4.2.1", excerpt: "Minimum 3 years of relevant industry experience required.", relevance: 0.94 },
        { page: 6, section: "4.3", excerpt: "Annual turnover must exceed $5 million USD equivalent.", relevance: 0.91 },
      ],
    };
  }

  return {
    content: `I don't have specific information about "${question}" in this tender document. Try asking about the submission deadline, technical qualifications, or scope of work.`,
    sources: undefined,
  };
};

export default function AskPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const tenderId = id === "new" || !id ? "1777415229182" : id;
  const [messages, setMessages] = useState<RAGMessage[]>([]);
  const [query, setQuery] = useState("");
  const [querying, setQuerying] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleQuery = async (question?: string) => {
    const userQuery = question || query.trim();
    if (!userQuery || querying) return;
    
    setQuery("");
    setQuerying(true);

    await new Promise((resolve) => setTimeout(resolve, 1200));
    
    const answer = getAnswer(userQuery);
    
    const newMessages: RAGMessage[] = [
      ...messages,
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
        content: answer.content,
        sources: answer.sources,
        created_at: new Date().toISOString(),
      },
    ];
    setMessages(newMessages);
    setQuerying(false);
  };

  const handleClearHistory = () => {
    setMessages([]);
  };

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
            Clear
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
              <p className="text-sm text-[#434655] max-w-md mb-6">
                Get instant answers to questions about the tender document.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {presetQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuery(q)}
                    disabled={querying}
                    className="text-sm px-4 py-2 rounded-full border border-[#C3C6D7] bg-white text-[#434655] hover:bg-[#F2F3FF] hover:border-[#004AC6] transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
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
          <form onSubmit={(e) => { e.preventDefault(); handleQuery(); }} className="flex gap-3">
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