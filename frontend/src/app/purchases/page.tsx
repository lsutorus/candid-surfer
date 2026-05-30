"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import Link from "next/link";

interface PurchaseItem {
  id: string;
  session_id: string;
  amount_cents: number;
  created_at: string;
  session_start_time: string;
  session_thumbnail_url: string | null;
  spot_name: string;
}

interface PurchaseListResponse {
  purchases: PurchaseItem[];
}

interface DownloadLinks {
  links: Record<string, string>;
}

function DownloadButton({ sessionId }: { sessionId: string }) {
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [total, setTotal] = useState(0);
  const { getAccessToken } = useAuth();

  const startDownload = async () => {
    setDownloading(true);
    setProgress(0);

    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Not authenticated");

      const data = await apiFetch<DownloadLinks>(
        `/api/sessions/${sessionId}/download-links`,
        { token },
      );

      const entries = Object.entries(data.links);
      setTotal(entries.length);

      for (let i = 0; i < entries.length; i++) {
        const [clipId, url] = entries[i];
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Download failed for clip ${clipId}`);

        const blob = await res.blob();
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `${sessionId}_${clipId}.mp4`;
        a.click();
        URL.revokeObjectURL(a.href);
        setProgress(i + 1);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <button
      onClick={startDownload}
      disabled={downloading}
      className="rounded bg-primary px-3 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
    >
      {downloading
        ? `Downloading ${progress}/${total}...`
        : "Download Clips"}
    </button>
  );
}

export default function PurchasesPage() {
  const { user, getAccessToken, loading } = useAuth();

  const { data, status } = useQuery<PurchaseListResponse>({
    queryKey: ["purchases"],
    queryFn: async () => {
      const token = await getAccessToken();
      if (!token) throw new Error("Not authenticated");
      return apiFetch<PurchaseListResponse>("/api/purchases", { token });
    },
    enabled: !!user,
  });

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="max-w-md rounded-lg border bg-card p-8 text-center shadow-sm">
          <h1 className="text-2xl font-bold">My Purchases</h1>
          <p className="mt-2 text-muted-foreground">
            Please log in to view your purchases.
          </p>
          <Link
            href="/auth/login"
            className="mt-6 inline-block rounded bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Log In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-bold">My Purchases</h1>

      {status === "pending" && (
        <p className="mt-4 text-muted-foreground">Loading...</p>
      )}
      {status === "error" && (
        <p className="mt-4 text-destructive">Failed to load purchases</p>
      )}

      {data && data.purchases.length === 0 && (
        <p className="mt-4 text-muted-foreground">No purchases yet.</p>
      )}

      {data && data.purchases.length > 0 && (
        <div className="mt-4 flex flex-col gap-3">
          {data.purchases.map((p) => (
            <div
              key={p.id}
              className="flex items-center gap-4 rounded-lg border bg-card p-4 shadow-sm"
            >
              {p.session_thumbnail_url ? (
                <img
                  src={p.session_thumbnail_url}
                  alt="Thumbnail"
                  className="h-16 w-28 rounded object-cover"
                />
              ) : (
                <div className="flex h-16 w-28 items-center justify-center rounded bg-muted text-xs text-muted-foreground">
                  No thumbnail
                </div>
              )}
              <div className="flex flex-1 flex-col gap-1">
                <span className="text-sm font-medium">{p.spot_name}</span>
                <span className="text-xs text-muted-foreground">
                  {new Date(p.session_start_time).toLocaleDateString()}
                </span>
                <span className="text-sm font-semibold">
                  ${(p.amount_cents / 100).toFixed(2)}
                </span>
              </div>
              <DownloadButton sessionId={p.session_id} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
