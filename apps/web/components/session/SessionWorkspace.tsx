"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { SafeMarkdown } from "@/components/ui/SafeMarkdown";
import {
  ApiError,
  fetchArtifact,
  patchSessionPhase,
  postArchitectureRun,
  postChat,
} from "@/lib/api/client";
import { pollUntilAssistantCountExceeds } from "@/lib/api/poll";
import { useSessionBundle } from "@/lib/hooks";
import type { ArtifactDetail, ArtifactMeta } from "@/lib/types";

type Props = { sessionId: string };

function formatArtifactLabel(a: ArtifactMeta): string {
  return `${a.artifact_type} v${a.version}`;
}

function tryPrettyContent(content: string): { text: string; isJson: boolean } {
  const t = content.trim();
  if (!t.startsWith("{") && !t.startsWith("[")) {
    return { text: content, isJson: false };
  }
  try {
    return { text: JSON.stringify(JSON.parse(t), null, 2), isJson: true };
  } catch {
    return { text: content, isJson: false };
  }
}

export function SessionWorkspace({ sessionId }: Props) {
  const {
    session,
    messages,
    artifacts,
    loading,
    error: loadError,
    refresh,
  } = useSessionBundle(sessionId);
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(
    null,
  );
  const [artifactDetail, setArtifactDetail] = useState<ArtifactDetail | null>(
    null,
  );
  const [draft, setDraft] = useState("");
  const [archNotes, setArchNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [pollNote, setPollNote] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedArtifactId) {
      setArtifactDetail(null);
      return;
    }
    let cancelled = false;
    void fetchArtifact(sessionId, selectedArtifactId)
      .then((a) => {
        if (!cancelled) setArtifactDetail(a);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setActionError(
            e instanceof ApiError ? e.message : "Failed to load artifact",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId, selectedArtifactId]);

  const hasPrd = useMemo(
    () => artifacts.some((a) => a.artifact_type === "prd"),
    [artifacts],
  );

  const assistantCount = useMemo(
    () => messages.filter((m) => m.role === "assistant").length,
    [messages],
  );

  const sendChat = async (productAction: "default" | "synthesize_prd") => {
    const text =
      draft.trim() ||
      (productAction === "synthesize_prd"
        ? "Please synthesize the PRD from the conversation so far."
        : "");
    if (!text) return;
    setBusy(true);
    setActionError(null);
    setPollNote(null);
    const acBefore = assistantCount;
    try {
      const out = await postChat(sessionId, text, productAction);
      setDraft("");
      if (out.status === 202) {
        setPollNote("Run queued — waiting for assistant message…");
        await pollUntilAssistantCountExceeds(sessionId, acBefore);
        await refresh();
        setPollNote(null);
      } else {
        await refresh();
      }
    } catch (e: unknown) {
      setActionError(e instanceof ApiError ? e.message : "Chat failed");
    } finally {
      setBusy(false);
    }
  };

  const goArchitecture = async () => {
    setBusy(true);
    setActionError(null);
    try {
      await patchSessionPhase(sessionId, "architecture");
      await refresh();
    } catch (e: unknown) {
      setActionError(
        e instanceof ApiError ? e.message : "Could not change phase",
      );
    } finally {
      setBusy(false);
    }
  };

  const runArchitecture = async () => {
    setBusy(true);
    setActionError(null);
    setPollNote(null);
    const acBefore = assistantCount;
    try {
      const out = await postArchitectureRun(
        sessionId,
        archNotes.trim() || undefined,
      );
      setArchNotes("");
      if (out.status === 202) {
        setPollNote("Architecture run queued — waiting for assistant message…");
        await pollUntilAssistantCountExceeds(sessionId, acBefore);
        await refresh();
        setPollNote(null);
      } else {
        await refresh();
      }
    } catch (e: unknown) {
      setActionError(
        e instanceof ApiError ? e.message : "Architecture run failed",
      );
    } finally {
      setBusy(false);
    }
  };

  if (loading || !session) {
    return (
      <div className="p-6 text-sm text-black/60 dark:text-white/60">
        Loading session…
      </div>
    );
  }

  const displayContent = artifactDetail
    ? tryPrettyContent(artifactDetail.content)
    : null;

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <div className="flex min-h-[45vh] flex-1 flex-col border-b border-black/10 md:min-h-screen md:border-b-0 md:border-r dark:border-white/10">
        <header className="flex flex-wrap items-center gap-2 border-b border-black/10 px-4 py-3 dark:border-white/10">
          <Link
            href="/"
            className="text-sm text-blue-600 underline dark:text-blue-400"
          >
            ← Sessions
          </Link>
          <span className="text-black/30 dark:text-white/30">|</span>
          <h1 className="text-sm font-semibold">
            {session.title?.trim() || "Untitled session"}
          </h1>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              session.phase === "architecture"
                ? "bg-violet-500/20 text-violet-800 dark:text-violet-200"
                : "bg-emerald-500/20 text-emerald-800 dark:text-emerald-200"
            }`}
          >
            {session.phase === "architecture" ? "Architecture" : "Product"}
          </span>
        </header>

        {loadError && (
          <div className="mx-4 mt-3 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-800 dark:text-red-200">
            {loadError}
          </div>
        )}
        {actionError && (
          <div className="mx-4 mt-3 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-900 dark:text-amber-100">
            {actionError}
          </div>
        )}
        {pollNote && (
          <div className="mx-4 mt-3 rounded-lg border border-blue-500/40 bg-blue-500/10 px-3 py-2 text-sm text-blue-800 dark:text-blue-200">
            {pollNote}
          </div>
        )}

        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`rounded-lg border px-3 py-2 text-sm ${
                m.role === "user"
                  ? "ml-4 border-blue-500/30 bg-blue-500/5"
                  : "mr-4 border-black/10 bg-black/3 dark:border-white/10 dark:bg-white/5"
              }`}
            >
              <div className="mb-1 text-xs font-medium uppercase text-black/50 dark:text-white/50">
                {m.role}
              </div>
              <SafeMarkdown content={m.content} />
            </div>
          ))}
        </div>

        <div className="border-t border-black/10 p-4 dark:border-white/10">
          {session.phase === "product" && (
            <div className="mb-2 flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => void sendChat("synthesize_prd")}
                className="rounded-lg border border-black/15 bg-black/5 px-3 py-1.5 text-xs font-medium dark:border-white/20 dark:bg-white/10"
              >
                Force PRD synthesis
              </button>
              {hasPrd && session.phase === "product" && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void goArchitecture()}
                  className="rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
                >
                  Move to architecture phase
                </button>
              )}
            </div>
          )}
          {session.phase === "architecture" && (
            <div className="mb-2 space-y-2">
              <textarea
                value={archNotes}
                onChange={(e) => setArchNotes(e.target.value)}
                placeholder="Optional notes for the architecture run…"
                rows={2}
                className="w-full resize-none rounded-lg border border-black/15 bg-transparent px-3 py-2 text-sm dark:border-white/20"
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => void runArchitecture()}
                className="rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
              >
                Run architecture pipeline
              </button>
            </div>
          )}
          <div className="flex gap-2">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Message…"
              rows={3}
              className="min-w-0 flex-1 resize-none rounded-lg border border-black/15 bg-transparent px-3 py-2 text-sm dark:border-white/20"
              disabled={busy}
            />
            <button
              type="button"
              disabled={busy}
              onClick={() => void sendChat("default")}
              className="self-end rounded-lg bg-black px-4 py-2 text-sm font-medium text-white dark:bg-white dark:text-black"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      <aside className="flex w-full flex-col md:w-[min(44vw,520px)] md:shrink-0">
        <div className="border-b border-black/10 px-4 py-3 dark:border-white/10">
          <h2 className="text-sm font-semibold">Artifacts</h2>
          <p className="text-xs text-black/50 dark:text-white/50">
            Select a version to view stored PRD / architecture outputs.
          </p>
        </div>
        <div className="flex flex-wrap gap-1 border-b border-black/10 p-2 dark:border-white/10">
          {artifacts.length === 0 && (
            <span className="text-xs text-black/50 dark:text-white/50">
              No artifacts yet.
            </span>
          )}
          {artifacts.map((a) => (
            <button
              key={a.id}
              type="button"
              onClick={() => setSelectedArtifactId(a.id)}
              className={`rounded-md px-2 py-1 text-xs ${
                selectedArtifactId === a.id
                  ? "bg-black text-white dark:bg-white dark:text-black"
                  : "bg-black/5 dark:bg-white/10"
              }`}
            >
              {formatArtifactLabel(a)}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {!artifactDetail && (
            <p className="text-sm text-black/50 dark:text-white/50">
              Choose an artifact to preview.
            </p>
          )}
          {displayContent && !displayContent.isJson && (
            <SafeMarkdown content={displayContent.text} />
          )}
          {displayContent && displayContent.isJson && (
            <pre className="overflow-x-auto rounded-lg bg-black/6 p-3 font-mono text-xs dark:bg-white/10">
              {displayContent.text}
            </pre>
          )}
        </div>
      </aside>
    </div>
  );
}
