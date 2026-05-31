"use client";

import { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from "react-leaflet";
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

// Grey icon for unapproved spots (admin map only)
const GreyIcon = L.icon({
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  className: "greyscale-marker",
});

interface SpotMapProps {
  spots: Spot[];
  activeSpotId: string | null;
  onSpotSelect: (id: string) => void;
  onBoundsChange: (bounds: L.LatLngBounds) => void;
  pickingCoords?: boolean;
  onMapClick?: (lat: number, lng: number) => void;
  /** Show approved vs unapproved with different markers (admin view) */
  showApprovalStatus?: boolean;
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

function MapClickHandler({
  enabled,
  onClick,
}: {
  enabled: boolean;
  onClick: (lat: number, lng: number) => void;
}) {
  useMapEvents({
    click(e) {
      if (enabled) {
        onClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });
  return null;
}

export default function SpotMap({
  spots,
  activeSpotId,
  onSpotSelect,
  onBoundsChange,
  pickingCoords = false,
  onMapClick,
  showApprovalStatus = false,
}: SpotMapProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return (
    <>
      {showApprovalStatus && (
        <style>{`
          .greyscale-marker {
            filter: grayscale(1) opacity(0.5);
          }
        `}</style>
      )}
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
        <MapClickHandler enabled={pickingCoords} onClick={onMapClick ?? (() => {})} />
        <MarkerClusterGroup chunkedLoading>
          {spots.map((spot) => (
            <Marker
              key={spot.id}
              position={[spot.lat, spot.lng]}
              icon={showApprovalStatus && !spot.is_approved ? GreyIcon : DefaultIcon}
              eventHandlers={{
                click: () => onSpotSelect(spot.id),
              }}
            />
          ))}
        </MarkerClusterGroup>
      </MapContainer>
    </>
  );
}
