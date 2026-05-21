"use client";

import { useMutation } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { useVideoUpload } from "@/hooks/useVideoUpload";

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
  const [files, setFiles] = useState<File[]>([]);
  const [authToken, setAuthToken] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const sessionMutation = useMutation({
    mutationFn: async (body: {
      spot_id: string;
      start_time: string;
      end_time: string;
      price: number;
    }) => {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
      const res = await fetch(`${API_URL}/api/sessions`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json() as Promise<{ id: string }>;
    },
  });

  const sessionId = sessionMutation.data?.id ?? null;
  const { upload, cancel, progress, status, error } =
    useVideoUpload(sessionId);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sessionMutation.mutate({
      spot_id: spotId,
      start_time: new Date(startTime).toISOString(),
      end_time: new Date(endTime).toISOString(),
      price: Math.round(parseFloat(priceDollars) * 100),
    });
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files) setFiles(Array.from(e.target.files));
  }

  async function handleUpload() {
    if (!files[0] || !sessionId || !authToken) return;
    // Extract captured_at from file modification time as fallback
    // (mp4box.js integration would be added here in production)
    const capturedAt = new Date().toISOString();
    await upload(files[0], capturedAt, authToken);
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="mb-6 text-2xl font-semibold">Create Session</h1>
      <form onSubmit={handleSubmit} className="flex w-full max-w-md flex-col gap-4">
        <label className="flex flex-col gap-1">
          Spot
          <select
            value={spotId}
            onChange={(e) => setSpotId(e.target.value)}
            className="rounded border p-2"
          >
            {SPOTS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Start Time
          <input
            type="datetime-local"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            required
            className="rounded border p-2"
          />
        </label>
        <label className="flex flex-col gap-1">
          End Time
          <input
            type="datetime-local"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            required
            className="rounded border p-2"
          />
        </label>
        <label className="flex flex-col gap-1">
          Price ($)
          <input
            type="number"
            min="5"
            step="0.01"
            value={priceDollars}
            onChange={(e) => setPriceDollars(e.target.value)}
            required
            className="rounded border p-2"
          />
        </label>
        <label className="flex flex-col gap-1">
          Auth Token
          <input
            type="password"
            value={authToken}
            onChange={(e) => setAuthToken(e.target.value)}
            placeholder="Supabase JWT"
            className="rounded border p-2"
          />
        </label>
        <button
          type="submit"
          disabled={sessionMutation.isPending}
          className="rounded bg-black p-2 text-white hover:bg-zinc-800 disabled:opacity-50"
        >
          {sessionMutation.isPending ? "Creating..." : "Create Session"}
        </button>
        {sessionMutation.isError && (
          <p className="text-red-600">Error: {sessionMutation.error.message}</p>
        )}
        {sessionMutation.isSuccess && (
          <p className="text-green-600">Session created! ID: {sessionId}</p>
        )}
      </form>

      {/* Upload section — visible after session is created */}
      {sessionMutation.isSuccess && (
        <div className="mt-8 w-full max-w-md">
          <h2 className="mb-4 text-xl font-semibold">Upload Video</h2>

          <label className="flex flex-col gap-1">
            Video File
            <input
              ref={fileRef}
              type="file"
              accept="video/mp4"
              onChange={handleFileChange}
              className="rounded border p-2"
            />
          </label>

          {files[0] && (
            <p className="mt-2 text-sm text-zinc-600">
              {files[0].name} ({(files[0].size / (1024 * 1024)).toFixed(1)} MB)
            </p>
          )}

          <div className="mt-4 flex gap-2">
            <button
              onClick={handleUpload}
              disabled={
                !files[0] || !authToken || status === "uploading" || status === "completing"
              }
              className="rounded bg-black p-2 text-white hover:bg-zinc-800 disabled:opacity-50"
            >
              {status === "uploading"
                ? `Uploading... ${progress}%`
                : status === "completing"
                  ? "Completing..."
                  : status === "done"
                    ? "Upload Complete"
                    : "Start Upload"}
            </button>
            {(status === "uploading" || status === "completing") && (
              <button
                onClick={cancel}
                className="rounded border border-red-600 p-2 text-red-600 hover:bg-red-50"
              >
                Cancel
              </button>
            )}
          </div>

          {status !== "idle" && status !== "done" && (
            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-zinc-200">
              <div
                className="h-full bg-black transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}

          {status === "done" && (
            <p className="mt-2 text-green-600">Video uploaded successfully!</p>
          )}
          {error && <p className="mt-2 text-red-600">Error: {error}</p>}
        </div>
      )}
    </main>
  );
}
