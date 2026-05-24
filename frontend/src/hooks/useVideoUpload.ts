"use client";

import { useCallback, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";

const CHUNK_SIZE = 10 * 1024 * 1024; // 10 MB
const MAX_CONCURRENT = 3;

interface CompletedPart {
  PartNumber: number;
  ETag: string;
}

interface UploadState {
  uploadId: string;
  key: string;
  clipId: string;
  fileName: string;
  fileSize: number;
  completedParts: number[];
}

interface InitiateResponse {
  clip_id: string;
  upload_id: string;
  key: string;
}

interface PresignResponse {
  [partNumber: string]: string;
}

function storageKey(sessionId: string, fileName: string, fileSize: number) {
  return `upload:${sessionId}:${fileName}:${fileSize}`;
}

function loadState(
  sessionId: string,
  fileName: string,
  fileSize: number,
): UploadState | null {
  try {
    const raw = localStorage.getItem(storageKey(sessionId, fileName, fileSize));
    return raw ? (JSON.parse(raw) as UploadState) : null;
  } catch {
    return null;
  }
}

function saveState(
  sessionId: string,
  state: UploadState,
): void {
  localStorage.setItem(
    storageKey(sessionId, state.fileName, state.fileSize),
    JSON.stringify(state),
  );
}

function clearState(
  sessionId: string,
  fileName: string,
  fileSize: number,
): void {
  localStorage.removeItem(storageKey(sessionId, fileName, fileSize));
}

export function useVideoUpload(sessionId: string | null) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<
    "idle" | "uploading" | "completing" | "done" | "error"
  >("idle");
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const completedPartsRef = useRef<Map<number, CompletedPart>>(new Map());

  const upload = useCallback(
    async (
      file: File,
      capturedAt: string,
      token: string,
    ) => {
      if (!sessionId) throw new Error("No session ID");
      const sid = sessionId;

      abortRef.current = new AbortController();
      completedPartsRef.current = new Map();
      setStatus("uploading");
      setError(null);
      setProgress(0);

      const totalParts = Math.ceil(file.size / CHUNK_SIZE);

      // Check for resumable state
      const saved = loadState(sid, file.name, file.size);
      let uploadId: string;
      let key: string;
      let clipId: string;

      if (saved) {
        uploadId = saved.uploadId;
        key = saved.key;
        clipId = saved.clipId;
        saved.completedParts.forEach((pn) => {
          // Re-upload parts since ETags aren't persisted
        });
        clearState(sid, file.name, file.size);
      }

      // Step 1: Initiate
      const init = await apiFetch<InitiateResponse>(
        "/api/clips/multipart/initiate",
        {
          method: "POST",
          token,
          body: JSON.stringify({
            session_id: sessionId,
            filename: file.name,
            file_size: file.size,
            captured_at: capturedAt,
          }),
        },
      );
      uploadId = init.upload_id;
      key = init.key;
      clipId = init.clip_id;

      const uploadState: UploadState = {
        uploadId,
        key,
        clipId: clipId,
        fileName: file.name,
        fileSize: file.size,
        completedParts: [],
      };

      // Step 2: Chunk, presign, and upload in parallel batches
      const allPartNumbers = Array.from({ length: totalParts }, (_, i) => i + 1);
      let nextIndex = 0;

      async function uploadPart(partNumber: number): Promise<void> {
        const start = (partNumber - 1) * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const blob = file.slice(start, end);

        const presign = await apiFetch<PresignResponse>(
          "/api/clips/multipart/presign-parts",
          {
            method: "POST",
            token,
            body: JSON.stringify({
              key,
              upload_id: uploadId,
              part_numbers: [partNumber],
            }),
          },
        );

        const url = presign[String(partNumber)];
        if (!url) throw new Error(`No presigned URL for part ${partNumber}`);

        const res = await fetch(url, {
          method: "PUT",
          body: blob,
          signal: abortRef.current?.signal,
        });

        if (!res.ok) {
          throw new Error(`Part ${partNumber} upload failed: ${res.status}`);
        }

        const etag = res.headers.get("ETag");
        if (!etag) {
          throw new Error(`No ETag returned for part ${partNumber}`);
        }

        completedPartsRef.current.set(partNumber, {
          PartNumber: partNumber,
          ETag: etag,
        });

        uploadState.completedParts = [...completedPartsRef.current.keys()];
        saveState(sid, uploadState);

        const completed = completedPartsRef.current.size;
        setProgress(Math.round((completed / totalParts) * 100));
      }

      async function worker(): Promise<void> {
        while (nextIndex < allPartNumbers.length) {
          const idx = nextIndex++;
          const partNumber = allPartNumbers[idx];
          await uploadPart(partNumber);
        }
      }

      try {
        await Promise.all(
          Array.from({ length: Math.min(MAX_CONCURRENT, totalParts) }, () =>
            worker(),
          ),
        );
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Upload failed";
        setStatus("error");
        setError(msg);
        return;
      }

      // Step 3: Complete
      setStatus("completing");
      const parts = Array.from(completedPartsRef.current.values()).sort(
        (a, b) => a.PartNumber - b.PartNumber,
      );

      try {
        await apiFetch<{ status: string }>(
          "/api/clips/multipart/complete",
          {
            method: "POST",
            token,
            body: JSON.stringify({
              clip_id: clipId,
              upload_id: uploadId,
              key,
              parts,
            }),
          },
        );
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Complete failed";
        setStatus("error");
        setError(msg);
        return;
      }

      clearState(sid, file.name, file.size);
      setProgress(100);
      setStatus("done");
    },
    [sessionId],
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
    setProgress(0);
  }, []);

  return { upload, cancel, progress, status, error };
}
