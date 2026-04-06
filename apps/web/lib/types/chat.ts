/** Chat / architecture run payloads from POST responses. */

export type ChatResult = {
  user_message_id: string;
  assistant_message_id: string;
  assistant_content: string;
  prd_artifact_id?: string | null;
  prd_version?: number | null;
  phase1_ready_for_architecture?: boolean | null;
};

export type QueuedAgentRun = {
  correlation_id: string;
  idempotency_key: string;
  user_message_id?: string | null;
  status: "queued";
};

export type ArchitectureRunResult = {
  user_message_id?: string | null;
  assistant_message_id: string;
  assistant_content: string;
  artifacts: { artifact_type: string; id: string; version: number }[];
};
