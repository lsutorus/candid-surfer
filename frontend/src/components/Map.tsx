"use client";

import dynamic from "next/dynamic";

const SpotMap = dynamic(() => import("./SpotMap"), { ssr: false });

export default function Map(props: {
  activeSpotId: string | null;
  onSpotSelect: (id: string) => void;
}) {
  return <SpotMap {...props} />;
}
