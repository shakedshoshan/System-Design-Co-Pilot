"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, fetchSessions } from "@/lib/api/client";
import type { SessionRow } from "@/lib/types";

export type SessionsListState = {
  sessions: SessionRow[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
};

/** Load `/api/v1/sessions` for the home list. */
export function useSessionsList(): SessionsListState {
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const rows = await fetchSessions();
      setSessions(rows);
    } catch (e: unknown) {
      setError(
        e instanceof ApiError
          ? e.message
          : "Could not load sessions. Is the API running and NEXT_PUBLIC_API_URL set?",
      );
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    void refresh()
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(
            e instanceof ApiError
              ? e.message
              : "Could not load sessions. Is the API running and NEXT_PUBLIC_API_URL set?",
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

  return { sessions, loading, error, refresh };
}
