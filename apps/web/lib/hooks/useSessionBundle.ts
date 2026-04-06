"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, fetchArtifactMetas, fetchMessages, fetchSession } from "@/lib/api/client";
import type { ArtifactMeta, MessageRow, SessionRow } from "@/lib/types";

export type SessionBundleState = {
  session: SessionRow | null;
  messages: MessageRow[];
  artifacts: ArtifactMeta[];
  loading: boolean;
  error: string | null;
  /** Reload session header, messages, and artifact list (does not toggle `loading`). */
  refresh: () => Promise<void>;
};

/** Parallel fetch for the session workspace (chat + artifact sidebar). */
export function useSessionBundle(sessionId: string): SessionBundleState {
  const [session, setSession] = useState<SessionRow | null>(null);
  const [messages, setMessages] = useState<MessageRow[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [sess, msgs, arts] = await Promise.all([
      fetchSession(sessionId),
      fetchMessages(sessionId),
      fetchArtifactMetas(sessionId),
    ]);
    setSession(sess);
    setMessages(msgs);
    setArtifacts(arts);
  }, [sessionId]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    void refresh()
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(
            e instanceof ApiError
              ? e.message
              : e instanceof Error
                ? e.message
                : "Failed to load session",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  return {
    session,
    messages,
    artifacts,
    loading,
    error,
    refresh,
  };
}
