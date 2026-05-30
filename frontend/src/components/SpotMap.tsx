"use client";

import { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Marker, useMap } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import type { Spot } from "@/hooks/useSpotsByBounds";

// Fix default marker icon paths broken by Next.js bundler
const DefaultIcon = L.icon({
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

interface SpotMapProps {
  spots: Spot[];
  activeSpotId: string | null;
  onSpotSelect: (id: string) => void;
  onBoundsChange: (bounds: L.LatLngBounds) => void;
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

export default function SpotMap({ spots, activeSpotId, onSpotSelect, onBoundsChange }: SpotMapProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return (
    <MapContainer
      center={[33.3853, -119.5828]}
      zoom={5}
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <BoundsTracker onBoundsChange={onBoundsChange} />
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
