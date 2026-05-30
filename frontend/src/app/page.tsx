"use client";

import { useState } from "react";
import type { LatLngBounds } from "leaflet";
import Map from "@/components/Map";
import SessionFeed from "@/components/SessionFeed";
import { useSpotsByBounds } from "@/hooks/useSpotsByBounds";

export default function Home() {
  const [activeSpotId, setActiveSpotId] = useState<string | null>(null);
  const [bounds, setBounds] = useState<LatLngBounds | null>(null);
  const { data: spots = [] } = useSpotsByBounds(bounds);

  return (
    <div className="flex flex-1 flex-col md:flex-row">
      <div className="h-80 md:h-full md:w-1/2">
        <Map
          spots={spots}
          activeSpotId={activeSpotId}
          onSpotSelect={setActiveSpotId}
          onBoundsChange={setBounds}
        />
      </div>
      <div className="flex-1 border-t md:border-t-0 md:border-l">
        <SessionFeed spotId={activeSpotId} />
      </div>
    </div>
  );
}
