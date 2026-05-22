"use client";

import { useState } from "react";
import Map from "@/components/Map";
import SessionFeed from "@/components/SessionFeed";

export default function Home() {
  const [activeSpotId, setActiveSpotId] = useState<string | null>(null);

  return (
    <main className="flex h-screen flex-col md:flex-row">
      <div className="h-1/2 md:h-full md:w-1/2">
        <Map activeSpotId={activeSpotId} onSpotSelect={setActiveSpotId} />
      </div>
      <div className="h-1/2 md:h-full md:w-1/2 border-t md:border-t-0 md:border-l">
        <SessionFeed spotId={activeSpotId} />
      </div>
    </main>
  );
}
