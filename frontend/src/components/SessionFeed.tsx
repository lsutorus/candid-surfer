"use client";

import { useState } from "react";
import { useInfiniteQuery, useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import Player from "@/components/Player";

interface Session {
  id: string;
  spot_id: string;
  filmer_id: string;
  start_time: string;
  end_time: string;
  price: number;
  thumbnail_url: string | null;
  clip_status: string;
  created_at: string;
}

interface SessionFeedResponse {
  sessions: Session[];
  next_cursor: string | null;
}

interface SessionFeedProps {
  spotId: string | null;
}

export default function SessionFeed({ spotId }: SessionFeedProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [buyingId, setBuyingId] = useState<string | null>(null);
  const { user, getAccessToken } = useAuth();

  const checkoutMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const token = await getAccessToken();
      if (!token) throw new Error("Not authenticated");
      return apiFetch<{ url: string }>("/api/purchases/checkout", {
        method: "POST",
        token,
        body: JSON.stringify({ session_id: sessionId }),
      });
    },
    onSuccess: (data) => {
      window.location.href = data.url;
    },
  });

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, status } =
    useInfiniteQuery<SessionFeedResponse>({
      queryKey: ["sessions", spotId],
      queryFn: ({ pageParam }) => {
        const params = new URLSearchParams({ limit: "10" });
        if (spotId) params.set("spot_id", spotId);
        if (pageParam) params.set("cursor", pageParam as string);
        return apiFetch<SessionFeedResponse>(`/api/sessions?${params}`);
      },
      initialPageParam: null as string | null,
      getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
      enabled: spotId !== null,
    });

  const sessions = data?.pages.flatMap((p) => p.sessions) ?? [];

  if (!spotId) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        Select a spot on the map to view sessions
      </div>
    );
  }

  if (status === "pending") {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        Loading sessions...
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex h-full items-center justify-center text-destructive">
        Failed to load sessions
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        No sessions at this spot yet
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-4">
      {sessions.map((s) => (
        <div
          key={s.id}
          className="flex flex-col gap-2 rounded-lg border bg-card p-3 shadow-sm cursor-pointer hover:bg-accent/50 transition-colors"
          onClick={() => setSelectedId(selectedId === s.id ? null : s.id)}
        >
          <div className="flex gap-3">
            {s.thumbnail_url ? (
              <img
                src={s.thumbnail_url}
                alt="Session thumbnail"
                className="h-20 w-32 rounded object-cover"
              />
            ) : (
              <div className="flex h-20 w-32 items-center justify-center rounded bg-muted text-xs text-muted-foreground">
                No thumbnail
              </div>
            )}
            <div className="flex flex-col justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {new Date(s.start_time).toLocaleDateString(undefined, {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                  })}
                </span>
                {s.clip_status !== "ready" && (
                  <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700">
                    {s.clip_status === "failed" ? "Failed" : "Processing"}
                  </span>
                )}
              </div>
              <span className="text-lg font-semibold">
                ${(s.price / 100).toFixed(2)}
              </span>
              {user ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setBuyingId(s.id);
                    checkoutMutation.mutate(s.id);
                  }}
                  disabled={checkoutMutation.isPending && buyingId === s.id}
                  className="rounded bg-primary px-3 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {checkoutMutation.isPending && buyingId === s.id
                    ? "Redirecting..."
                    : "Buy"}
                </button>
              ) : (
                <a
                  href="/auth/login"
                  className="text-xs text-zinc-500 underline"
                >
                  Log in to purchase
                </a>
              )}
              {checkoutMutation.isError && buyingId === s.id && (
                <span className="text-xs text-destructive">
                  {checkoutMutation.error.message}
                </span>
              )}
            </div>
          </div>
          {selectedId === s.id && <Player sessionId={s.id} />}
        </div>
      ))}
      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
          className="rounded-lg border px-4 py-2 text-sm hover:bg-accent disabled:opacity-50"
        >
          {isFetchingNextPage ? "Loading..." : "Load more"}
        </button>
      )}
    </div>
  );
}
