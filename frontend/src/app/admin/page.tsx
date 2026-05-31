"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { LatLngBounds } from "leaflet";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import Link from "next/link";
import Map from "@/components/Map";
import type { Spot } from "@/hooks/useSpotsByBounds";

export default function AdminPage() {
  const { user, getAccessToken, loading } = useAuth();
  const queryClient = useQueryClient();
  const [activeSpotId, setActiveSpotId] = useState<string | null>(null);
  const [bounds, setBounds] = useState<LatLngBounds | null>(null);

  // Fetch all spots (approved + pending) for admin map
  const { data: allSpots = [], status: allStatus } = useQuery<Spot[]>({
    queryKey: ["admin-spots-all"],
    queryFn: async () => {
      const token = await getAccessToken();
      if (!token) throw new Error("Not authenticated");
      return apiFetch<Spot[]>("/api/admin/spots", { token });
    },
    enabled: !!user,
  });

  // Fetch pending-only for the list
  const { data: pendingSpots = [] } = useQuery<Spot[]>({
    queryKey: ["admin-spots-pending"],
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
      queryClient.invalidateQueries({ queryKey: ["admin-spots-all"] });
      queryClient.invalidateQueries({ queryKey: ["admin-spots-pending"] });
      queryClient.invalidateQueries({ queryKey: ["spots"] });
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

  const activeSpot = allSpots.find((s) => s.id === activeSpotId);

  return (
    <div className="flex flex-1 flex-col lg:flex-row">
      {/* Map: blue markers = approved, grey = pending */}
      <div className="h-96 lg:h-full lg:w-1/2">
        <Map
          spots={allSpots}
          activeSpotId={activeSpotId}
          onSpotSelect={setActiveSpotId}
          onBoundsChange={setBounds}
          showApprovalStatus
        />
      </div>

      {/* Spot list */}
      <div className="flex-1 border-t lg:border-t-0 lg:border-l">
        <div className="mx-auto max-w-xl px-4 py-6">
          <h1 className="text-2xl font-bold">Admin — Pending Spots</h1>

          {allStatus === "error" && (
            <p className="mt-4 text-red-600">Failed to load spots (not admin?)</p>
          )}

          {/* Selected spot detail */}
          {activeSpot && !activeSpot.is_approved && (
            <div className="mt-4 rounded-lg border-2 border-amber-400 bg-amber-50 p-4">
              <h2 className="text-lg font-semibold">{activeSpot.name}</h2>
              <p className="text-sm text-zinc-600">
                {activeSpot.lat.toFixed(4)}, {activeSpot.lng.toFixed(4)} · {activeSpot.timezone}
              </p>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => approveMutation.mutate(activeSpot.id)}
                  disabled={approveMutation.isPending}
                  className="rounded bg-green-600 px-4 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50"
                >
                  {approveMutation.isPending ? "..." : "Approve"}
                </button>
                <button
                  onClick={() => setActiveSpotId(null)}
                  className="rounded border px-4 py-1.5 text-sm text-zinc-600 hover:bg-zinc-100"
                >
                  Deselect
                </button>
              </div>
            </div>
          )}

          {/* Pending spots list */}
          {pendingSpots.length === 0 && allStatus === "success" && (
            <p className="mt-4 text-zinc-500">No pending spots.</p>
          )}

          {pendingSpots.length > 0 && (
            <div className="mt-4 flex flex-col gap-2">
              {pendingSpots.map((spot) => (
                <div
                  key={spot.id}
                  onClick={() => setActiveSpotId(spot.id === activeSpotId ? null : spot.id)}
                  className={`flex cursor-pointer items-center gap-4 rounded-lg border bg-white p-4 shadow-sm transition-colors hover:bg-zinc-50 ${
                    spot.id === activeSpotId ? "border-amber-400" : ""
                  }`}
                >
                  <div className="flex flex-1 flex-col gap-1">
                    <span className="text-sm font-medium">{spot.name}</span>
                    <span className="text-xs text-zinc-500">
                      {spot.lat.toFixed(4)}, {spot.lng.toFixed(4)} · {spot.timezone}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      approveMutation.mutate(spot.id);
                    }}
                    disabled={approveMutation.isPending}
                    className="rounded bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-50"
                  >
                    {approveMutation.isPending ? "..." : "Approve"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
