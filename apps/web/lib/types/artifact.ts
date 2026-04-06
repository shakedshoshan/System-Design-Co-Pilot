/** Versioned outputs from `GET .../artifacts` and `GET .../artifacts/{id}`. */

export type ArtifactMeta = {
  id: string;
  artifact_type: string;
  version: number;
  created_at: string;
};

export type ArtifactDetail = ArtifactMeta & {
  session_id: string;
  content: string;
};
