"use client";

import Link from "next/link";
import { useState } from "react";

import { ApiError, createSession } from "@/lib/api/client";
import { useSessionsList } from "@/lib/hooks";

export default function HomePage() {
  const { sessions, loading, error: listError, refresh } = useSessionsList();
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const onNew = async () => {
    setBusy(true);
    setActionError(null);
    try {
      const s = await createSession();
      window.location.href = `/sessions/${s.id}`;
    } catch (e: unknown) {
      setActionError(
        e instanceof ApiError ? e.message : "Failed to create session",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col px-4 py-8">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            System Design Co-Pilot
          </h1>
          <p className="text-sm text-black/60 dark:text-white/60">
            Sessions — product phase (PRD) then architecture agents.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => void onNew()}
          className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white dark:bg-white dark:text-black"
        >
          New session
        </button>
      </header>

      {listError && (
        <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-800 dark:text-red-200">
          {listError}
          <button
            type="button"
            className="ml-3 underline"
            onClick={() => void refresh()}
          >
            Retry
          </button>
        </div>
      )}
      {actionError && (
        <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-800 dark:text-red-200">
          {actionError}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-black/60 dark:text-white/60">Loading…</p>
      ) : sessions.length === 0 ? (
        <p className="text-sm text-black/60 dark:text-white/60">
          No sessions yet. Create one to start.
        </p>
      ) : (
        <ul className="space-y-2">
          {sessions.map((s) => (
            <li key={s.id}>
              <Link
                href={`/sessions/${s.id}`}
                className="flex flex-col rounded-lg border border-black/10 px-4 py-3 transition hover:bg-black/[0.03] dark:border-white/10 dark:hover:bg-white/5"
              >
                <span className="font-medium">
                  {s.title?.trim() || "Untitled session"}
                </span>
                <span className="text-xs text-black/50 dark:text-white/50">
                  {s.phase} ·{" "}
                  {s.updated_at
                    ? new Date(s.updated_at).toLocaleString()
                    : s.id.slice(0, 8)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
