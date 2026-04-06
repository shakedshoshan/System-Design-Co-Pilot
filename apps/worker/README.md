# Kafka worker

Consumes `architecture_copilot_events` and runs Phase 1 / Phase 2 LangGraph jobs produced by the API when `KAFKA_ASYNC_RUNS=true`.

Run from the **repository root** (same `.env` as the API):

```bash
poetry run worker
```

Requires `DATABASE_URL`, `OPENAI_API_KEY`, `KAFKA_BOOTSTRAP_SERVERS`, and matching `KAFKA_TOPIC_EVENTS` / `KAFKA_CONSUMER_GROUP` as the API.
