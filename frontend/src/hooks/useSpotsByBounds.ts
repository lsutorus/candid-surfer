"use client";

import { useQuery } from "@tanstack/react-query";
import type L from "leaflet";
import { apiFetch } from "@/lib/api";

export interface Spot {
  id: string;
  name: string;
  lat: number;
  lng: number;
  timezone: string;
  is_approved: boolean;
}

export function useSpotsByBounds(bounds: L.LatLngBounds | null) {
  return useQuery<Spot[]>({
    queryKey: [
      "spots",
      bounds?.getSouthWest().lat,
      bounds?.getNorthEast().lat,
      bounds?.getSouthWest().lng,
      bounds?.getNorthEast().lng,
    ],
    queryFn: () => {
      const sw = bounds!.getSouthWest();
      const ne = bounds!.getNorthEast();
      return apiFetch<Spot[]>(
        `/api/spots?min_lat=${sw.lat}&max_lat=${ne.lat}&min_lng=${sw.lng}&max_lng=${ne.lng}`,
      );
    },
    enabled: bounds !== null,
    staleTime: 30_000,
  });
}
