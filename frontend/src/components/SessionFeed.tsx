"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface Session {
  id: string;
  spot_id: string;
  filmer_id: string;
  start_time: string;
  end_time: string;
  price: number;
  thumbnail_url: string | null;
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
          className="flex gap-3 rounded-lg border bg-card p-3 shadow-sm"
        >
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
            <span className="text-sm text-muted-foreground">
              {new Date(s.start_time).toLocaleDateString(undefined, {
                weekday: "short",
                month: "short",
                day: "numeric",
              })}
            </span>
            <span className="text-lg font-semibold">
              ${(s.price / 100).toFixed(2)}
            </span>
          </div>
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
