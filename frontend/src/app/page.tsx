"use client";

import { useState } from "react";
import Map from "@/components/Map";
import SessionFeed from "@/components/SessionFeed";

export default function Home() {
  const [activeSpotId, setActiveSpotId] = useState<string | null>(null);

  return (
    <div className="flex flex-1 flex-col md:flex-row">
      <div className="h-80 md:h-full md:w-1/2">
        <Map activeSpotId={activeSpotId} onSpotSelect={setActiveSpotId} />
      </div>
      <div className="flex-1 border-t md:border-t-0 md:border-l">
        <SessionFeed spotId={activeSpotId} />
      </div>
    </div>
  );
}
