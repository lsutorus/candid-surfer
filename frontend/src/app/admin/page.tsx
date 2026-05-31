"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import Link from "next/link";
import type { Spot } from "@/hooks/useSpotsByBounds";

export default function AdminPage() {
  const { user, getAccessToken, loading } = useAuth();
  const queryClient = useQueryClient();

  const { data: spots = [], status } = useQuery<Spot[]>({
    queryKey: ["admin-spots"],
    queryFn: async () => {
      const token = await getAccessToken();
      if (!token) throw new Error("Not authenticated");
      return apiFetch<Spot[]>("/api/admin/spots?is_approved=false", { token });
    },
    enabled: !!user,
  });

  const approveMutation = useMutation({
    mutationFn: async (spotId: string) => {
      const token = await getAccessToken();
      if (!token) throw new Error("Not authenticated");
      return apiFetch<Spot>(`/api/admin/spots/${spotId}`, {
        method: "PATCH",
        token,
        body: JSON.stringify({ is_approved: true }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-spots"] });
      queryClient.invalidateQueries({ queryKey: ["spots"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async (spotId: string) => {
      const token = await getAccessToken();
      if (!token) throw new Error("Not authenticated");
      return apiFetch<Spot>(`/api/admin/spots/${spotId}`, {
        method: "PATCH",
        token,
        body: JSON.stringify({ is_approved: false }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-spots"] });
    },
  });

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-zinc-500">
        Loading...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="max-w-md rounded-lg border bg-white p-8 text-center shadow">
          <h1 className="text-2xl font-bold">Admin</h1>
          <p className="mt-2 text-zinc-600">Please log in to access admin.</p>
          <Link
            href="/auth/login"
            className="mt-6 inline-block rounded bg-black px-6 py-2 text-sm text-white hover:bg-zinc-800"
          >
            Log In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-bold">Admin — Pending Spots</h1>

      {status === "pending" && (
        <p className="mt-4 text-zinc-500">Loading...</p>
      )}
      {status === "error" && (
        <p className="mt-4 text-red-600">Failed to load spots (not admin?)</p>
      )}

      {spots.length === 0 && status === "success" && (
        <p className="mt-4 text-zinc-500">No pending spots.</p>
      )}

      {spots.length > 0 && (
        <div className="mt-4 flex flex-col gap-3">
          {spots.map((spot) => (
            <div
              key={spot.id}
              className="flex items-center gap-4 rounded-lg border bg-white p-4 shadow-sm"
            >
              <div className="flex flex-1 flex-col gap-1">
                <span className="text-sm font-medium">{spot.name}</span>
                <span className="text-xs text-zinc-500">
                  {spot.lat.toFixed(4)}, {spot.lng.toFixed(4)} · {spot.timezone}
                </span>
              </div>
              <button
                onClick={() => approveMutation.mutate(spot.id)}
                disabled={approveMutation.isPending}
                className="rounded bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-50"
              >
                {approveMutation.isPending ? "..." : "Approve"}
              </button>
              <button
                onClick={() => rejectMutation.mutate(spot.id)}
                disabled={rejectMutation.isPending}
                className="rounded bg-red-600 px-3 py-1 text-xs text-white hover:bg-red-700 disabled:opacity-50"
              >
                {rejectMutation.isPending ? "..." : "Reject"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
