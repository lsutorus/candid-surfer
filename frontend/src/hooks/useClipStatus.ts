"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

interface ClipStatus {
  clip_id: string;
  status: string;
}

interface SessionStatusResponse {
  clips: ClipStatus[];
  aggregate: string; // uploading | uploaded | processing | ready | failed | partial
}

const POLL_MS = 5000;

export function useClipStatus(
  sessionId: string | null,
  enabled: boolean,
) {
  const { getAccessToken } = useAuth();
  const shouldPoll = !!sessionId && enabled;

  return useQuery<SessionStatusResponse>({
    queryKey: ["session-status", sessionId],
    queryFn: async () => {
      const token = await getAccessToken();
      return apiFetch<SessionStatusResponse>(`/api/sessions/${sessionId}/status`, {
        token: token ?? undefined,
      });
    },
    enabled: shouldPoll,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return POLL_MS;
      const active = ["uploading", "uploaded", "processing", "partial"];
      return active.includes(data.aggregate) ? POLL_MS : false;
    },
    refetchIntervalInBackground: false,
  });
}
