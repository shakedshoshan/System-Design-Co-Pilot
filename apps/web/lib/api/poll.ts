import { fetchMessages } from "@/lib/api/client";
import type { MessageRow } from "@/lib/types";

/**
 * Poll until a new assistant message appears (HTTP 202 + Kafka worker path).
 */
export async function pollUntilAssistantCountExceeds(
  sessionId: string,
  previousAssistantCount: number,
  options?: { maxMs?: number; intervalMs?: number },
): Promise<MessageRow[]> {
  const maxMs = options?.maxMs ?? 120_000;
  const intervalMs = options?.intervalMs ?? 2000;
  const start = Date.now();
  while (Date.now() - start < maxMs) {
    await new Promise((r) => setTimeout(r, intervalMs));
    const messages = await fetchMessages(sessionId);
    const ac = messages.filter((m) => m.role === "assistant").length;
    if (ac > previousAssistantCount) return messages;
  }
  return fetchMessages(sessionId);
}
