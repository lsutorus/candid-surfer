"use client";

import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { apiFetch } from "@/lib/api";
import type { Spot } from "@/hooks/useSpotsByBounds";

const TIMEZONES = [
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Anchorage",
  "Pacific/Honolulu",
  "America/Phoenix",
  "Europe/London",
  "Europe/Paris",
  "Asia/Tokyo",
  "Australia/Sydney",
];

interface SpotSuggestFormProps {
  lat?: number;
  lng?: number;
  onCreated?: (spot: Spot) => void;
  onCancel?: () => void;
}

export default function SpotSuggestForm({
  lat: initialLat,
  lng: initialLng,
  onCreated,
  onCancel,
}: SpotSuggestFormProps) {
  const { getAccessToken, user } = useAuth();
  const [name, setName] = useState("");
  const [lat, setLat] = useState(initialLat?.toString() ?? "");
  const [lng, setLng] = useState(initialLng?.toString() ?? "");
  const [timezone, setTimezone] = useState("America/Los_Angeles");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!user) {
    return (
      <div className="flex flex-col gap-2 p-4">
        <p className="text-sm text-zinc-600">Log in to suggest a spot.</p>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);
    if (isNaN(latNum) || latNum < -90 || latNum > 90) {
      setError("Latitude must be between -90 and 90");
      return;
    }
    if (isNaN(lngNum) || lngNum < -180 || lngNum > 180) {
      setError("Longitude must be between -180 and 180");
      return;
    }

    setLoading(true);
    try {
      const token = await getAccessToken();
      const spot = await apiFetch<Spot>("/api/spots", {
        method: "POST",
        token: token ?? undefined,
        body: JSON.stringify({
          name,
          lat: latNum,
          lng: lngNum,
          timezone,
        }),
      });
      onCreated?.(spot);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to suggest spot");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 p-4">
      <h2 className="text-lg font-semibold">Suggest a spot</h2>

      <label className="flex flex-col gap-1">
        Name
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="Pipeline, Oahu"
          className="rounded border p-2"
        />
      </label>

      <div className="flex gap-2">
        <label className="flex flex-1 flex-col gap-1">
          Latitude
          <input
            type="number"
            step="any"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            required
            className="rounded border p-2"
          />
        </label>
        <label className="flex flex-1 flex-col gap-1">
          Longitude
          <input
            type="number"
            step="any"
            value={lng}
            onChange={(e) => setLng(e.target.value)}
            required
            className="rounded border p-2"
          />
        </label>
      </div>

      <p className="text-xs text-zinc-500">
        Click the map to set coordinates, or type them manually.
      </p>

      <label className="flex flex-col gap-1">
        Timezone
        <select
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          className="rounded border p-2"
        >
          {TIMEZONES.map((tz) => (
            <option key={tz} value={tz}>
              {tz}
            </option>
          ))}
        </select>
      </label>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 rounded bg-black p-2 text-white hover:bg-zinc-800 disabled:opacity-50"
        >
          {loading ? "Submitting..." : "Suggest spot"}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded border p-2 text-zinc-600 hover:bg-zinc-100"
          >
            Cancel
          </button>
        )}
      </div>

      {error && <p className="text-red-600">{error}</p>}
    </form>
  );
}
