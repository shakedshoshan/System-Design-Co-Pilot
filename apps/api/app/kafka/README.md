# Kafka — architecture co-pilot events

**Full guide:** [KAFKA.md](./KAFKA.md) (what Kafka is, envelopes, API + worker implementation).

## Topic

- Default topic name: **`architecture_copilot_events`** (`Settings.kafka_topic_events`, see `topics.py`).
- Messages are UTF-8 JSON **envelopes** (`envelope.py`) with `schema_version: 1`, discriminated by `event_type`.

## Event types (Step 7)

| `event_type` | When |
|--------------|------|
| `session.created` | After `POST /api/v1/sessions` when `KAFKA_ENABLED=true`. |
| `message.submitted` | Async mode: API enqueues Phase 1 or Phase 2 work (`KAFKA_ASYNC_RUNS=true`). |
| `agent.run.started` / `agent.run.completed` | Emitted by the worker around graph execution. |
| `artifact.updated` | Emitted by the worker after each new artifact row (PRD or architecture_*). |

## Local dev

1. `docker compose up` (Kafka on `localhost:9092`).
2. `KAFKA_ENABLED=true` and, for async HTTP + background processing, `KAFKA_ASYNC_RUNS=true`.
3. Run API: `poetry run api` (from repo root).
4. Run worker: `poetry run worker`.
5. After `202` responses, poll `GET /api/v1/sessions/{id}/messages` for the assistant reply.

Partition key: `session_id` (ordering per session).
