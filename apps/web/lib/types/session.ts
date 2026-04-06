/** `DesignSession` rows from GET list / GET one. */

export type SessionRow = {
  id: string;
  title: string | null;
  phase: string;
  updated_at?: string;
};
