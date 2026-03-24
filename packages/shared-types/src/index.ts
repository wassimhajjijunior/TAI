export type Chunk = {
  id: string;
  document_id: string;
  content: string;
  content_translated: string;
  embedding: number[];
  position: number;
  page_number: number;
};

export type RagQueryRequest = {
  document_id: string;
  query: string;
  top_k: number;
};

export type RagChunkResult = {
  chunk_id: string;
  content: string;
  similarity_score: number;
};

export type RagQueryResponse = {
  document_id: string;
  results: RagChunkResult[];
};

export type GenerateResponseRequest = {
  document_id: string;
  language: "fr" | "ar" | "en";
  instructions?: string;
};

export type Citation = {
  chunk_id: string;
  excerpt: string;
};

export type ResponseRecord = {
  id: string;
  document_id: string;
  content: string;
  citations: Citation[];
};

export type UpdateResponseRequest = {
  content: string;
  citations: Citation[];
};

export type ExportRequest = {
  format: "docx" | "pdf";
  response_id: string;
};

export type ExportRecord = {
  id: string;
  document_id: string;
  response_id: string;
  format: "docx" | "pdf";
  file_path: string;
};
