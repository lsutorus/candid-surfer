"use client";

import { useState, useCallback } from "react";
import type { LatLngBounds } from "leaflet";
import Map from "@/components/Map";
import SessionFeed from "@/components/SessionFeed";
import SpotSuggestForm from "@/components/SpotSuggestForm";
import { useSpotsByBounds } from "@/hooks/useSpotsByBounds";
import type { Spot } from "@/hooks/useSpotsByBounds";
import { useQueryClient } from "@tanstack/react-query";

export default function Home() {
  const [activeSpotId, setActiveSpotId] = useState<string | null>(null);
  const [bounds, setBounds] = useState<LatLngBounds | null>(null);
  const { data: spots = [] } = useSpotsByBounds(bounds);

  const [suggestOpen, setSuggestOpen] = useState(false);
  const [pickedLat, setPickedLat] = useState<number | undefined>();
  const [pickedLng, setPickedLng] = useState<number | undefined>();
  const [pickingCoords, setPickingCoords] = useState(false);
  const queryClient = useQueryClient();

  const handleMapClick = useCallback((lat: number, lng: number) => {
    setPickedLat(lat);
    setPickedLng(lng);
    setPickingCoords(false);
  }, []);

  function handleSpotCreated(_spot: Spot) {
    setSuggestOpen(false);
    setPickedLat(undefined);
    setPickedLng(undefined);
    // Invalidate spots query so new spot appears
    queryClient.invalidateQueries({ queryKey: ["spots"] });
  }

  return (
    <div className="flex flex-1 flex-col md:flex-row">
      <div className="relative h-80 md:h-full md:w-1/2">
        <Map
          spots={spots}
          activeSpotId={activeSpotId}
          onSpotSelect={setActiveSpotId}
          onBoundsChange={setBounds}
          pickingCoords={pickingCoords}
          onMapClick={handleMapClick}
        />

        {/* Suggest a spot button */}
        {!suggestOpen && (
          <button
            onClick={() => setSuggestOpen(true)}
            className="absolute right-3 top-3 z-[1000] rounded bg-black px-3 py-1.5 text-sm text-white shadow hover:bg-zinc-800"
          >
            + Suggest a spot
          </button>
        )}

        {/* Picking coords bar */}
        {suggestOpen && pickingCoords && (
          <div className="absolute left-1/2 top-3 z-[1000] -translate-x-1/2 rounded bg-white px-4 py-2 text-sm shadow">
            Click the map to pick coordinates
          </div>
        )}

        {/* Suggest form overlay */}
        {suggestOpen && (
          <div className="absolute right-3 top-12 z-[1000] w-72 rounded border bg-white shadow-lg">
            <div className="flex items-center justify-between border-b px-4 py-2">
              <span className="text-sm font-medium">New spot</span>
              <button
                onClick={() => {
                  setSuggestOpen(false);
                  setPickingCoords(false);
                  setPickedLat(undefined);
                  setPickedLng(undefined);
                }}
                className="text-zinc-500 hover:text-zinc-700"
              >
                ✕
              </button>
            </div>
            <div className="mb-2 px-4 pt-2">
              <button
                type="button"
                onClick={() => setPickingCoords(!pickingCoords)}
                className={`rounded px-3 py-1 text-xs ${
                  pickingCoords
                    ? "bg-blue-600 text-white"
                    : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
                }`}
              >
                {pickingCoords ? "Click map..." : "Pick on map"}
              </button>
            </div>
            <SpotSuggestForm
              lat={pickedLat}
              lng={pickedLng}
              onCreated={handleSpotCreated}
              onCancel={() => {
                setSuggestOpen(false);
                setPickingCoords(false);
                setPickedLat(undefined);
                setPickedLng(undefined);
              }}
            />
          </div>
        )}
      </div>
      <div className="flex-1 border-t md:border-t-0 md:border-l">
        <SessionFeed spotId={activeSpotId} />
      </div>
    </div>
  );
}
