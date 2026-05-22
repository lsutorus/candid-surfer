"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { MapContainer, TileLayer, Marker, useMap } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import { apiFetch } from "@/lib/api";

// Fix default marker icon paths broken by webpack
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

interface Spot {
  id: string;
  name: string;
  lat: number;
  lng: number;
  timezone: string;
  is_approved: boolean;
}

interface SpotMapProps {
  activeSpotId: string | null;
  onSpotSelect: (id: string) => void;
}

function BoundsTracker({
  onBoundsChange,
}: {
  onBoundsChange: (bounds: L.LatLngBounds) => void;
}) {
  const map = useMap();
  const isFirst = useRef(true);

  useEffect(() => {
    const handler = () => onBoundsChange(map.getBounds());
    if (isFirst.current) {
      handler();
      isFirst.current = false;
    }
    map.on("moveend", handler);
    return () => {
      map.off("moveend", handler);
    };
  }, [map, onBoundsChange]);

  return null;
}

export default function SpotMap({ activeSpotId, onSpotSelect }: SpotMapProps) {
  const [bounds, setBounds] = useState<L.LatLngBounds | null>(null);

  const { data: spots = [] } = useQuery<Spot[]>({
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

  const handleBoundsChange = (b: L.LatLngBounds) => setBounds(b);

  return (
    <MapContainer
      center={[33.75, -118.2]}
      zoom={10}
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <BoundsTracker onBoundsChange={handleBoundsChange} />
      <MarkerClusterGroup chunkedLoading>
        {spots.map((spot) => (
          <Marker
            key={spot.id}
            position={[spot.lat, spot.lng]}
            eventHandlers={{
              click: () => onSpotSelect(spot.id),
            }}
          />
        ))}
      </MarkerClusterGroup>
      {activeSpotId && (
        <style>{`
          .leaflet-marker-icon[title] { filter: none; }
        `}</style>
      )}
    </MapContainer>
  );
}
