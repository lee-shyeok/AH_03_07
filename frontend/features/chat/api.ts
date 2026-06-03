// 챗봇 API (REQ-CHAT-001/005)
import { apiFetch } from "@/lib/api/client";

export interface ChatMessage {
  id?: number | string;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

export async function createSession(): Promise<string> {
  const res = await apiFetch<{ session_id: string | number }>(
    "/v1/chat/sessions",
    { method: "POST" }
  );
  return String(res.session_id);
}

export async function getMessages(sessionId: string): Promise<ChatMessage[]> {
  const res = await apiFetch<
    { items?: ChatMessage[]; messages?: ChatMessage[] } | ChatMessage[]
  >(`/v1/chat/sessions/${sessionId}/messages`);
  if (Array.isArray(res)) return res;
  return res.items ?? res.messages ?? [];
}

export async function sendMessage(
  sessionId: string,
  content: string
): Promise<ChatMessage> {
  return apiFetch<ChatMessage>(`/v1/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    body: { content },
  });
}
