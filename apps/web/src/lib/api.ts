/**
 * API client for RAG Assistant backend.
 * Uses NEXT_PUBLIC_API_BASE_URL and x-demo-key header.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const DEMO_KEY = process.env.NEXT_PUBLIC_DEMO_KEY || "";

const DEMO_USER_ID = "11111111-1111-1111-1111-111111111111";

function headers(): HeadersInit {
  const h: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (DEMO_KEY) {
    h["x-demo-key"] = DEMO_KEY;
  }
  return h;
}

export interface DocumentSummary {
  id: string;
  filename: string;
  status: "pending" | "uploaded" | "processing" | "ready" | "failed";
  page_count: number | null;
  error_message: string | null;
  created_at: string;
}

export interface PresignResponse {
  document_id: string;
  s3_key: string;
  upload_url: string;
  method: string;
}

export interface AskResponse {
  answer: string;
  citations: Array<{
    chunk_id: string;
    page_number: number;
    snippet: string;
  }>;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  const text = await res.text();
  let json: unknown = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    // ignore
  }
  if (!res.ok) {
    const detail =
      typeof json === "object" && json && "detail" in json
        ? (json as { detail?: unknown }).detail
        : text;
    throw new ApiError(
      res.statusText || "Request failed",
      res.status,
      detail
    );
  }
  return json as T;
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  const res = await fetch(
    `${API_BASE}/documents?user_id=${encodeURIComponent(DEMO_USER_ID)}`,
    { headers: headers() }
  );
  return handleResponse<DocumentSummary[]>(res);
}

export async function getDocument(id: string): Promise<DocumentSummary> {
  const res = await fetch(
    `${API_BASE}/documents/${id}?user_id=${encodeURIComponent(DEMO_USER_ID)}`,
    { headers: headers() }
  );
  return handleResponse<DocumentSummary>(res);
}

export async function presign(
  filename: string,
  fileSizeBytes: number
): Promise<PresignResponse> {
  const res = await fetch(`${API_BASE}/documents/presign`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      filename,
      content_type: "application/pdf",
      file_size_bytes: fileSizeBytes,
    }),
  });
  return handleResponse<PresignResponse>(res);
}

export async function uploadToPresignedUrl(
  uploadUrl: string,
  file: File
): Promise<void> {
  const res = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": "application/pdf" },
    body: file,
  });
  if (!res.ok) {
    throw new ApiError("Upload failed", res.status, await res.text());
  }
}

export async function confirmUpload(
  documentId: string,
  s3Key: string
): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/documents/confirm`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      document_id: documentId,
      s3_key: s3Key,
    }),
  });
  return handleResponse<{ status: string }>(res);
}

export async function ingestDocument(documentId: string): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/ingest`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ user_id: DEMO_USER_ID }),
  });
  return handleResponse<{ status: string }>(res);
}

export async function ask(
  documentId: string,
  question: string
): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      document_id: documentId,
      question,
    }),
  });
  return handleResponse<AskResponse>(res);
}
