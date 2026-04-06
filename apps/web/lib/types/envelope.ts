/** API success/error wrapper (`app/schemas/responses.py`). */

export type Meta = { request_id: string; timestamp: string };

export type ErrorEnvelope = {
  error: { code: string; message: string; details?: unknown };
  meta: Meta;
};

export type SuccessEnvelope<T> = { data: T; meta: Meta };
