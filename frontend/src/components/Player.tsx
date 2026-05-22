"use client";

import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

const CUSTOMER_CODE = process.env.NEXT_PUBLIC_CLOUDFLARE_CUSTOMER_CODE ?? "";

function streamUrl(uid: string) {
  return `https://customer-${CUSTOMER_CODE}.cloudflarestream.com/${uid}/manifest/video.m3u8`;
}

interface PlayerProps {
  sessionId: string;
}

export default function Player({ sessionId }: PlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);

  const { data: streamUids = [], status } = useQuery<string[]>({
    queryKey: ["clips", sessionId],
    queryFn: () => apiFetch<string[]>(`/api/sessions/${sessionId}/clips`),
  });

  const currentUid = streamUids[currentIdx] ?? null;

  useEffect(() => {
    if (!currentUid || !videoRef.current) return;

    const video = videoRef.current;
    const url = streamUrl(currentUid);

    if (hlsRef.current) {
      hlsRef.current.destroy();
    }

    if (Hls.isSupported()) {
      const hls = new Hls();
      hlsRef.current = hls;
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play();
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
      video.play();
    }
  }, [currentUid]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onEnded = () => {
      setCurrentIdx((i) => i + 1);
    };

    video.addEventListener("ended", onEnded);
    return () => video.removeEventListener("ended", onEnded);
  }, []);

  useEffect(() => {
    return () => {
      hlsRef.current?.destroy();
    };
  }, []);

  if (status === "pending") {
    return <div className="flex h-64 items-center justify-center text-muted-foreground">Loading clips...</div>;
  }

  if (status === "error") {
    return <div className="flex h-64 items-center justify-center text-destructive">Failed to load clips</div>;
  }

  if (streamUids.length === 0) {
    return <div className="flex h-64 items-center justify-center text-muted-foreground">No clips ready yet</div>;
  }

  if (currentIdx >= streamUids.length) {
    return <div className="flex h-64 items-center justify-center text-muted-foreground">Playback complete</div>;
  }

  return (
    <div className="w-full">
      <video
        ref={videoRef}
        className="w-full rounded-lg"
        controls
        playsInline
      />
      <div className="mt-2 text-xs text-muted-foreground">
        Clip {currentIdx + 1} of {streamUids.length}
      </div>
    </div>
  );
}
