## Infrastructure Overview

- **Vercel:** Hosts Next.js client (root directory `/frontend`). Active deployment. Connects to FastAPI backend via REST.
- **Railway:** Hosts FastAPI Docker container. Active deployment at `https://[RAILWAY_DOMAIN]`. Runs web server and daily cron jobs.
- **Supabase:** Managed PostgreSQL DB (accessed via Supavisor Transaction Pool URL, port 6543). Auth provider.
- **Cloudflare:**
  - R2: Holds raw video uploads (multipart presigned PUT ingest, presigned GET egress). 30-day bucket lifecycle auto-delete rule.
  - Stream: Holds HLS encode, hard-burned watermarks. Webhook fires to Railway.
- **Stripe:** Connect accounts for direct filmer payout. Hosted checkout sessions for purchases.


## Frontend Architecture (Next.js)

- **Framework:** Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui.
- **State Management:** TanStack Query handles all API fetching, caching, and cursor-based infinite scrolling.
- **Map Discovery:** `src/components/SpotMap.tsx` renders Leaflet map with `react-leaflet-cluster` grouping spots at high zoom. Dynamically imported via `src/components/Map.tsx` using `next/dynamic` with `ssr: false` (Leaflet requires `window`). Tracks bounds on `moveend`, fetches visible spots via TanStack Query using float box query (`min_lat`, `max_lat`, `min_lng`, `max_lng`). Marker click sets `activeSpotId`.
- **Session Feed:** `src/components/SessionFeed.tsx` accepts `spotId` prop, uses `useInfiniteQuery` to fetch `GET /api/sessions?spot_id=...&limit=10&cursor=...`. Renders cards (thumbnail, date, price). "Load more" paginates via `next_cursor`.
- **Discovery Page:** `src/app/page.tsx` — split layout: map top/left, feed bottom/right. Manages `activeSpotId`, passes to both.
- **Leaflet CSS:** Imported in `src/app/globals.css` via `@import "leaflet/dist/leaflet.css"`.
- **Player:** Custom `hls.js` component wraps HTML5 `<video>`. Soft-concatenates chronologically sorted clips within a Session. Pre-buffers next clip.
- **Upload Hook:** `src/hooks/useVideoUpload.ts` handles R2 multipart uploads. 10 MB chunks via `File.slice`, max 3 concurrent PUTs, localStorage resume state (matches file name+size to recover after tab reload), progress reporting. `src/lib/api.ts` provides shared `apiFetch` helper.


## Backend Architecture (FastAPI)

- **Framework:** FastAPI with `slowapi` rate limiting.
- **ORM:** SQLModel handles both API validation schemas and DB models. Alembic handles migrations.
- **Auth:** `HTTPBearer` extracts Bearer token, `python-jose` decodes JWT locally using `SUPABASE_JWT_SECRET`. Auto-upserts local `users` row on first verified request (id=JWT sub, email=JWT email).
- **Database:** Supabase PostgreSQL via psycopg3. `postgresql://` URLs auto-rewritten to `postgresql+psycopg://`.
- **R2 Client:** `app/r2.py` initializes a boto3 S3 client targeting `https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com` (`region_name="auto"`). Reads `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` from env. Enforces 5 GB max file size.
- **Stream Ingest:** `app/services/stream.py` triggers Cloudflare Stream copy-ingest via `POST /accounts/{id}/stream/copy`. Reads `CF_STREAM_ACCOUNT_ID`, `CF_STREAM_API_TOKEN`, `CF_STREAM_WATERMARK_UID` from env. Called as `BackgroundTask` from multipart complete endpoint.
- **Env Loading:** `python-dotenv` in `app/db.py`, `app/auth.py`, `app/r2.py`, `app/services/stream.py`, `app/routers/webhooks.py`, and `alembic/env.py` loads `.env` before reading env vars. Missing critical vars raise `RuntimeError` with setup instructions.
- **Async Processing:** FastAPI `BackgroundTasks` used for non-blocking outbound API calls (e.g., triggering Cloudflare Stream ingest after R2 upload).
- **Routers:**
  - `/api/spots` — GET returns spots within bounding box (`min_lat`, `max_lat`, `min_lng`, `max_lng`). No auth. Float math query.
  - `/api/sessions` — POST creates session, requires auth, enforces $5 minimum price. GET lists sessions with cursor-based pagination, optional `spot_id` filter.
  - `/api/sessions/{session_id}/download-links` — GET returns presigned R2 download URLs for purchased session. Requires auth. Verifies Purchase row exists.
  - `/api/clips/multipart` — R2 multipart upload (initiate, presign-parts, complete). Requires auth. 5 GB file size limit. Complete endpoint triggers Stream ingest as background task.
  - `/api/webhooks/cloudflare` — Cloudflare Stream webhook. HMAC-SHA256 signature verification. Updates clip status and session thumbnail.
  - `/api/webhooks/stripe` — Stripe webhook. Signature verification via `stripe.Webhook.construct_event`. Idempotency via `stripe_events` table. Handles `checkout.session.completed` to record purchases.
  - `/api/purchases/checkout` — POST creates Stripe Checkout Session with Connect transfer_data (20% platform fee). Requires auth. Validates filmer has `stripe_account_id`.
- **Seed Script:** `scripts/seed.py` inserts approved spots (Pipeline, Lowers, Uluwatu).
