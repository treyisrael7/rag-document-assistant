"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  listDocuments,
  presign,
  uploadToPresignedUrl,
  confirmUpload,
  ingestDocument,
  ApiError,
  type DocumentSummary,
} from "@/lib/api";

const POLL_INTERVAL_MS = 2000;

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  uploaded: "Uploaded",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "text-amber-600 bg-amber-50",
  uploaded: "text-blue-600 bg-blue-50",
  processing: "text-indigo-600 bg-indigo-50 animate-pulse",
  ready: "text-emerald-600 bg-emerald-50",
  failed: "text-red-600 bg-red-50",
};

export default function DashboardPage() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>("");
  const [processingId, setProcessingId] = useState<string | null>(null);

  const fetchDocs = useCallback(async () => {
    try {
      setError(null);
      const list = await listDocuments();
      setDocs(list);
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? String(e.detail || e.message)
          : `Failed to load documents${e instanceof Error ? `: ${e.message}` : ""}`;
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  // Poll while any document is processing
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hasProcessing = docs.some((d) => d.status === "processing");
  useEffect(() => {
    if (!hasProcessing) return;
    pollRef.current = setInterval(fetchDocs, POLL_INTERVAL_MS);
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [hasProcessing, fetchDocs]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || file.type !== "application/pdf") {
      setError("Please select a PDF file.");
      return;
    }
    setUploading(true);
    setError(null);
    setUploadProgress("Getting upload URL...");

    try {
      const { document_id, s3_key, upload_url } = await presign(
        file.name,
        file.size
      );
      setUploadProgress("Uploading to storage...");
      await uploadToPresignedUrl(upload_url, file);
      setUploadProgress("Confirming upload...");
      await confirmUpload(document_id, s3_key);
      setUploadProgress("Starting processing...");
      await ingestDocument(document_id);
      setProcessingId(document_id);
      setUploadProgress("");
      await fetchDocs();
    } catch (e) {
      setError(
        e instanceof ApiError
          ? String(e.detail || e.message)
          : "Upload failed"
      );
      setUploadProgress("");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleProcess = async (doc: DocumentSummary) => {
    if (doc.status !== "uploaded") return;
    setProcessingId(doc.id);
    setError(null);
    try {
      await ingestDocument(doc.id);
      await fetchDocs();
    } catch (e) {
      setError(
        e instanceof ApiError
          ? String(e.detail || e.message)
          : "Failed to start processing"
      );
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            RAG Assistant
          </h1>
          <p className="mt-1 text-slate-600">
            Upload PDFs and query with grounded answers.
          </p>
        </header>

        {/* Upload zone */}
        <section className="mb-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-800">Upload PDF</h2>
          <div className="mt-4">
            <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-8 transition hover:border-slate-400 hover:bg-slate-100">
              <input
                type="file"
                accept="application/pdf"
                onChange={handleFileSelect}
                disabled={uploading}
                className="hidden"
              />
              {uploading ? (
                <span className="text-sm text-slate-600">{uploadProgress}</span>
              ) : (
                <>
                  <svg
                    className="h-10 w-10 text-slate-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  <span className="mt-2 text-sm text-slate-600">
                    Click to select a PDF
                  </span>
                </>
              )}
            </label>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            PDF will be uploaded and queued for processing automatically.
          </p>
        </section>

        {/* Error display */}
        {error && (
          <div className="mb-6 rounded-lg bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Documents list */}
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <h2 className="border-b border-slate-200 px-6 py-4 text-lg font-semibold text-slate-800">
            Documents
          </h2>
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
            </div>
          ) : docs.length === 0 ? (
            <div className="py-16 text-center text-slate-500">
              No documents yet. Upload a PDF to get started.
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {docs.map((doc) => (
                <li
                  key={doc.id}
                  className="flex items-center justify-between gap-4 px-6 py-4"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-3">
                      <span className="truncate font-medium text-slate-900">
                        {doc.filename}
                      </span>
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          STATUS_COLORS[doc.status] ?? "text-slate-600 bg-slate-100"
                        }`}
                      >
                        {STATUS_LABELS[doc.status] ?? doc.status}
                      </span>
                      {doc.error_message && (
                        <span className="text-xs text-red-600" title={doc.error_message}>
                          Error
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {doc.page_count != null
                        ? `${doc.page_count} page${doc.page_count !== 1 ? "s" : ""}`
                        : "—"}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {doc.status === "uploaded" && (
                      <button
                        onClick={() => handleProcess(doc)}
                        disabled={processingId === doc.id}
                        className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                      >
                        {processingId === doc.id ? "Processing..." : "Process"}
                      </button>
                    )}
                    {doc.status === "ready" && (
                      <Link
                        href={`/documents/${doc.id}`}
                        className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
                      >
                        Chat
                      </Link>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
