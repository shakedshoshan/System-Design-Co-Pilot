/** Chat turn from `GET .../messages`. */

export type MessageRow = {
  id: string;
  role: string;
  content: string;
  created_at: string;
  extra?: Record<string, unknown> | null;
};
