import { SessionWorkspace } from "@/components/session/SessionWorkspace";

type PageProps = { params: Promise<{ id: string }> };

export default async function SessionPage({ params }: PageProps) {
  const { id } = await params;
  return <SessionWorkspace sessionId={id} />;
}
