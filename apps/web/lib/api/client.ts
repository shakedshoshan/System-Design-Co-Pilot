import type {
  ArchitectureRunResult,
  ArtifactDetail,
  ArtifactMeta,
  ChatResult,
  ErrorEnvelope,
  MessageRow,
  QueuedAgentRun,
  SessionRow,
  SuccessEnvelope,
} from "@/lib/types";

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId?: string;
  readonly details?: unknown;

  constructor(
    code: string,
    message: string,
    status: number,
    requestId?: string,
    details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.requestId = requestId;
    this.details = details;
  }
}

export function getBaseUrl(): string {
  const u = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!u) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  return u.replace(/\/$/, "");
}

/** Backend nests messages list as `data.messages.messages` (MessagesListResult inside key). */
export function normalizeMessagesPayload(
  data: Record<string, unknown>,
): MessageRow[] {
  const raw = data.messages;
  if (Array.isArray(raw)) return raw as MessageRow[];
  if (
    raw &&
    typeof raw === "object" &&
    Array.isArray((raw as { messages: unknown }).messages)
  ) {
    return (raw as { messages: MessageRow[] }).messages;
  }
  return [];
}

async function parseResponse<T>(
  res: Response,
): Promise<{ data: T; meta: SuccessEnvelope<T>["meta"] }> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    throw new ApiError(
      "invalid_json",
      "Response was not JSON",
      res.status,
      res.headers.get("X-Request-ID") ?? undefined,
    );
  }

  if (!res.ok) {
    const err = body as Partial<ErrorEnvelope>;
    const code = err.error?.code ?? "http_error";
    const message = err.error?.message ?? res.statusText;
    throw new ApiError(
      code,
      message,
      res.status,
      err.meta?.request_id ?? res.headers.get("X-Request-ID") ?? undefined,
      err.error?.details,
    );
  }

  const ok = body as SuccessEnvelope<T>;
  if (!ok.data || !ok.meta) {
    throw new ApiError(
      "invalid_envelope",
      "Success response missing data or meta",
      res.status,
      res.headers.get("X-Request-ID") ?? undefined,
    );
  }
  return { data: ok.data, meta: ok.meta };
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${getBaseUrl()}${path}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  const { data } = await parseResponse<T>(res);
  return data;
}

export async function apiPost<T>(path: string, json?: unknown): Promise<T> {
  const res = await fetch(`${getBaseUrl()}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: json !== undefined ? JSON.stringify(json) : undefined,
  });
  const { data } = await parseResponse<T>(res);
  return data;
}

export async function apiPatch<T>(path: string, json: unknown): Promise<T> {
  const res = await fetch(`${getBaseUrl()}${path}`, {
    method: "PATCH",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(json),
  });
  const { data } = await parseResponse<T>(res);
  return data;
}

export async function apiPostWithStatus<T>(
  path: string,
  json: unknown,
): Promise<{ status: number; data: T }> {
  const res = await fetch(`${getBaseUrl()}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(json),
  });
  const { data } = await parseResponse<T>(res);
  return { status: res.status, data };
}

export async function fetchSessions(): Promise<SessionRow[]> {
  const data = await apiGet<{ sessions: SessionRow[] }>("/api/v1/sessions");
  return data.sessions ?? [];
}

export async function createSession(
  title?: string,
): Promise<{ id: string; title: string | null; phase: string }> {
  const data = await apiPost<{
    session: { id: string; title: string | null; phase: string };
  }>("/api/v1/sessions", { title: title ?? null });
  return data.session;
}

export async function fetchSession(sessionId: string): Promise<SessionRow> {
  const data = await apiGet<{ session: SessionRow }>(
    `/api/v1/sessions/${sessionId}`,
  );
  return data.session;
}

export async function fetchMessages(sessionId: string): Promise<MessageRow[]> {
  const data = await apiGet<Record<string, unknown>>(
    `/api/v1/sessions/${sessionId}/messages?limit=500`,
  );
  return normalizeMessagesPayload(data);
}

export async function fetchArtifactMetas(
  sessionId: string,
): Promise<ArtifactMeta[]> {
  const data = await apiGet<{ artifacts: ArtifactMeta[] }>(
    `/api/v1/sessions/${sessionId}/artifacts`,
  );
  return data.artifacts ?? [];
}

export async function fetchArtifact(
  sessionId: string,
  artifactId: string,
): Promise<ArtifactDetail> {
  const data = await apiGet<{ artifact: ArtifactDetail }>(
    `/api/v1/sessions/${sessionId}/artifacts/${artifactId}`,
  );
  return data.artifact;
}

export async function postChat(
  sessionId: string,
  content: string,
  productAction: "default" | "synthesize_prd" = "default",
): Promise<{ status: number; chat?: ChatResult; queued?: QueuedAgentRun }> {
  const { status, data } = await apiPostWithStatus<
    Record<string, unknown> & {
      chat?: ChatResult;
      queued_agent_run?: QueuedAgentRun;
    }
  >(`/api/v1/sessions/${sessionId}/chat`, {
    content,
    product_action: productAction,
  });
  const d = data as {
    chat?: ChatResult;
    queued_agent_run?: QueuedAgentRun;
  };
  if (status === 202 && d.queued_agent_run) {
    return { status, queued: d.queued_agent_run };
  }
  return { status, chat: d.chat };
}

export async function patchSessionPhase(
  sessionId: string,
  phase: "architecture",
): Promise<{ id: string; title: string | null; phase: string }> {
  const data = await apiPatch<{
    session: { id: string; title: string | null; phase: string };
  }>(`/api/v1/sessions/${sessionId}`, { phase });
  return data.session;
}

export async function postArchitectureRun(
  sessionId: string,
  notes?: string,
): Promise<{
  status: number;
  result?: ArchitectureRunResult;
  queued?: QueuedAgentRun;
}> {
  const { status, data } = await apiPostWithStatus<
    Record<string, unknown> & {
      architecture_run?: ArchitectureRunResult;
      queued_agent_run?: QueuedAgentRun;
    }
  >(`/api/v1/sessions/${sessionId}/architecture/run`, {
    notes: notes?.trim() || null,
  });
  const d = data as {
    architecture_run?: ArchitectureRunResult;
    queued_agent_run?: QueuedAgentRun;
  };
  if (status === 202 && d.queued_agent_run) {
    return { status, queued: d.queued_agent_run };
  }
  return { status, result: d.architecture_run };
}
