"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getDocument,
  ask,
  ApiError,
  type DocumentSummary,
  type AskResponse,
} from "@/lib/api";

const POLL_INTERVAL_MS = 2000;
const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  uploaded: "Uploaded",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

export default function DocumentChatPage() {
  const params = useParams();
  const id = params.id as string;
  const [doc, setDoc] = useState<DocumentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [answerData, setAnswerData] = useState<AskResponse | null>(null);
  const [askError, setAskError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDoc = useCallback(async () => {
    try {
      setError(null);
      const d = await getDocument(id);
      setDoc(d);
      return d;
    } catch (e) {
      setError(
        e instanceof ApiError
          ? String(e.detail || e.message)
          : "Failed to load document"
      );
      return null;
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDoc();
  }, [fetchDoc]);

  // Poll while processing
  useEffect(() => {
    if (!doc || doc.status !== "processing") return;
    pollRef.current = setInterval(fetchDoc, POLL_INTERVAL_MS);
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [doc?.status, fetchDoc]); // eslint-disable-line react-hooks/exhaustive-deps -- doc omitted to avoid polling loop

  useEffect(() => {
    if (doc?.status !== "processing") {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    }
  }, [doc?.status]);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q || asking) return;
    setAsking(true);
    setAskError(null);
    setAnswerData(null);
    try {
      const res = await ask(id, q);
      setAnswerData(res);
    } catch (e) {
      setAskError(
        e instanceof ApiError
          ? String(e.detail || e.message)
          : "Request failed"
      );
    } finally {
      setAsking(false);
    }
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      </main>
    );
  }

  if (error || !doc) {
    return (
      <main className="min-h-screen bg-slate-50 px-4 py-8">
        <div className="mx-auto max-w-2xl">
          <Link
            href="/dashboard"
            className="text-sm text-indigo-600 hover:underline"
          >
            ← Back to dashboard
          </Link>
          <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
            {error || "Document not found"}
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <Link
              href="/dashboard"
              className="text-sm text-indigo-600 hover:underline"
            >
              ← Dashboard
            </Link>
            <h1 className="mt-1 truncate text-xl font-bold text-slate-900">
              {doc.filename}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                doc.status === "ready"
                  ? "bg-emerald-100 text-emerald-700"
                  : doc.status === "processing"
                    ? "bg-indigo-100 text-indigo-700 animate-pulse"
                    : doc.status === "failed"
                      ? "bg-red-100 text-red-700"
                      : "bg-slate-200 text-slate-700"
              }`}
            >
              {STATUS_LABELS[doc.status] ?? doc.status}
            </span>
            {doc.error_message && (
              <span
                className="max-w-[200px] truncate text-xs text-red-600"
                title={doc.error_message}
              >
                {doc.error_message}
              </span>
            )}
          </div>
        </header>

        {doc.status !== "ready" && (
          <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-800">
            {doc.status === "processing" && (
              <p className="text-sm">
                Document is being processed. This page will update automatically.
              </p>
            )}
            {doc.status === "failed" && doc.error_message && (
              <p className="text-sm">{doc.error_message}</p>
            )}
            {(doc.status === "uploaded" || doc.status === "pending") && (
              <p className="text-sm">Go to the dashboard and click Process.</p>
            )}
          </div>
        )}

        {doc.status === "ready" && (
          <>
            <form onSubmit={handleAsk} className="mb-6">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about this document..."
                  disabled={asking}
                  className="flex-1 rounded-lg border border-slate-300 px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-70"
                />
                <button
                  type="submit"
                  disabled={asking || !question.trim()}
                  className="rounded-lg bg-indigo-600 px-6 py-3 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {asking ? "..." : "Ask"}
                </button>
              </div>
            </form>

            {askError && (
              <div className="mb-6 rounded-lg bg-red-50 p-4 text-red-700">
                {askError}
              </div>
            )}

            {answerData && (
              <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
                  Answer
                </h2>
                <div className="prose prose-slate max-w-none text-slate-700">
                  {answerData.answer.split(/(\[\d+-c\d+\])/g).map((part, i) => {
                    const m = part.match(/^\[(\d+)-c(\d+)\]$/);
                    if (m) {
                      const idx = parseInt(m[2], 10) - 1;
                      const citation = answerData!.citations[idx];
                      return (
                        <sup
                          key={i}
                          className="cursor-help font-medium text-indigo-600"
                          title={citation?.snippet}
                        >
                          {part}
                        </sup>
                      );
                    }
                    return <span key={i}>{part}</span>;
                  })}
                </div>
                {answerData.citations.length > 0 && (
                  <div className="mt-6 border-t border-slate-100 pt-4">
                    <h3 className="mb-2 text-sm font-semibold text-slate-600">
                      Citations
                    </h3>
                    <ul className="space-y-2">
                      {answerData.citations.map((c) => (
                        <li
                          key={c.chunk_id}
                          className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600"
                        >
                          <span className="font-mono text-xs text-indigo-600">
                            [{c.chunk_id}]
                          </span>{" "}
                          Page {c.page_number}: {c.snippet}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}
