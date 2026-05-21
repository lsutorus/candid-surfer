"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SPOTS = [
  { id: "a1b2c3d4-0001-4000-8000-000000000001", name: "Pipeline, Hawaii" },
  { id: "a1b2c3d4-0002-4000-8000-000000000002", name: "Lowers, California" },
  { id: "a1b2c3d4-0003-4000-8000-000000000003", name: "Uluwatu, Bali" },
];

export default function NewSessionPage() {
  const [spotId, setSpotId] = useState(SPOTS[0].id);
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [priceDollars, setPriceDollars] = useState("5");

  const mutation = useMutation({
    mutationFn: async (body: {
      spot_id: string;
      start_time: string;
      end_time: string;
      price: number;
    }) => {
      const res = await fetch(`${API_URL}/api/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate({
      spot_id: spotId,
      start_time: new Date(startTime).toISOString(),
      end_time: new Date(endTime).toISOString(),
      price: Math.round(parseFloat(priceDollars) * 100),
    });
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="mb-6 text-2xl font-semibold">Create Session</h1>
      <form onSubmit={handleSubmit} className="flex w-full max-w-md flex-col gap-4">
        <label className="flex flex-col gap-1">
          Spot
          <select value={spotId} onChange={(e) => setSpotId(e.target.value)} className="rounded border p-2">
            {SPOTS.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Start Time
          <input type="datetime-local" value={startTime} onChange={(e) => setStartTime(e.target.value)} required className="rounded border p-2" />
        </label>
        <label className="flex flex-col gap-1">
          End Time
          <input type="datetime-local" value={endTime} onChange={(e) => setEndTime(e.target.value)} required className="rounded border p-2" />
        </label>
        <label className="flex flex-col gap-1">
          Price ($)
          <input type="number" min="5" step="0.01" value={priceDollars} onChange={(e) => setPriceDollars(e.target.value)} required className="rounded border p-2" />
        </label>
        <button type="submit" disabled={mutation.isPending} className="rounded bg-black p-2 text-white hover:bg-zinc-800 disabled:opacity-50">
          {mutation.isPending ? "Creating..." : "Create Session"}
        </button>
        {mutation.isError && <p className="text-red-600">Error: {mutation.error.message}</p>}
        {mutation.isSuccess && <p className="text-green-600">Created! ID: {mutation.data.id}</p>}
      </form>
    </main>
  );
}
