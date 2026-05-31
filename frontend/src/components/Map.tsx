"use client";

import dynamic from "next/dynamic";
import type L from "leaflet";
import type { Spot } from "@/hooks/useSpotsByBounds";

const SpotMap = dynamic(() => import("./SpotMap"), { ssr: false });

export default function Map(props: {
  spots: Spot[];
  activeSpotId: string | null;
  onSpotSelect: (id: string) => void;
  onBoundsChange: (bounds: L.LatLngBounds) => void;
  pickingCoords?: boolean;
  onMapClick?: (lat: number, lng: number) => void;
  showApprovalStatus?: boolean;
}) {
  return <SpotMap {...props} />;
}
