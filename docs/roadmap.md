# Roadmap

## Completed

- [x] Backend DB schema (Users, Spots, Sessions, Clips, Purchases, StripeEvents)
- [x] Backend API (spots, sessions, clips, webhooks, purchases, download-links)
- [x] Map Discovery (Leaflet + react-leaflet-cluster, bounding box query, spot markers)
- [x] Session Feed (cursor-based infinite scroll, spot filter, inline Player toggle)
- [x] Video Player (hls.js soft-concat, pre-buffer next clip, Cloudflare Stream HLS)
- [x] Auth UI (Supabase SSR, LoginForm, AuthProvider, proxy middleware, apiFetch JWT injection, protected upload route)
- [x] Backend JWT verification (ES256 JWKS via PyJWT, thread-safe cache, Supabase key rotation support)

## Pending

### Phase 2 — Upload UI
Build page to create session and trigger video upload hook.

- [x] Build `src/app/upload/page.tsx` with session creation form (spot picker, time range, price)
- [x] Wire `useVideoUpload.ts` hook to file input with chunked upload progress bar
- [x] Call `POST /api/sessions` then `POST /api/clips/multipart/*` sequence
- [x] Add resume-from-localStorage detection on page load
- [x] Show upload status (uploading → processing → ready) via polling or TanStack Query
- [x] End-to-end upload verified: R2 CORS policy configured (AllowedOrigins + ExposeHeaders: ETag), backend CORS_ORIGINS set to production Vercel domain

### Phase 2b — Stream Ingest Pipeline
Clips upload to R2 successfully but Cloudflare Stream ingest may fail silently (background task errors not surfaced). Clips stuck in "processing" status.

- [ ] Verify `trigger_cloudflare_ingest` background task succeeds (check Railway deploy logs after upload)
- [ ] Verify Cloudflare Stream webhook (`POST /api/webhooks/cloudflare`) is reachable from Stream (check webhook URL in Stream dashboard)
- [ ] Add logging/error recovery for failed Stream ingest background tasks
- [ ] Confirm end-to-end flow: upload → R2 → Stream ingest → webhook → clip status "ready"

### Phase 3 — Purchase UI
Wire Stripe buy button and download manager.

- [x] Add "Buy" button to session cards in SessionFeed
- [x] Call `POST /api/purchases/checkout`, redirect to Stripe Hosted Checkout
- [x] Handle checkout return (success/cancel URLs)
- [x] Build download manager page calling `GET /api/sessions/{id}/download-links`
- [x] Sequential download of presigned R2 URLs to local machine

### Phase 4 — Spot Suggestion
Build form for user to suggest spot.

- [ ] Add `POST /api/spots` endpoint (auth required, `is_approved=False` by default)
- [ ] Build `src/components/SpotSuggestForm.tsx` (name, lat/lng picker, timezone)
- [ ] Show "Suggest a spot" button on map view
- [ ] Display pending spots differently from approved spots (e.g., grey marker)

### Phase 5 — Admin
Build page to approve spots.

- [ ] Add `GET /api/admin/spots?is_approved=false` endpoint (auth + admin check)
- [ ] Add `PATCH /api/admin/spots/{id}` endpoint to set `is_approved=True`
- [ ] Build `src/app/admin/page.tsx` listing pending spots with approve/reject actions
- [ ] Add admin role check (e.g., `is_admin` column on Users or hardcoded allowlist)

### Phase 6 — TTL Cron
Build Python script to delete old clips.

- [ ] Build `backend/scripts/ttl_delete.py` querying Clips where `created_at` > 30 days and `is_deleted=False`
- [ ] Fire Cloudflare Stream API DELETE for each clip's `stream_uid`
- [ ] Mark `is_deleted=True` on DB rows (R2 auto-deleted by bucket lifecycle rule)
- [ ] Add Railway cron schedule to run daily
