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
- **Auth:** `@supabase/ssr` for cookie-based session management. `src/components/AuthProvider.tsx` wraps app, exposes `user`, `session`, `loading`, `getAccessToken()` via React context (`useAuth()` hook). `src/components/LoginForm.tsx` — login/signup toggle, email/password, redirects via `?redirect=` param. Login page at `/auth/login`.
- **Proxy (Middleware):** `src/proxy.ts` (Next.js 16 proxy convention, replaces deprecated middleware). Calls `src/lib/supabase/middleware.ts` `updateSession()` — refreshes Supabase tokens on every request. Protects `/sessions/new`, redirects unauthenticated users to `/auth/login?redirect=<path>`.
- **Supabase Clients:**
  - `src/lib/supabase/client.ts` — Browser client (`createBrowserClient`), singleton. Used by AuthProvider and LoginForm.
  - `src/lib/supabase/server.ts` — Server client (`createServerClient`), per-request. For future Server Components/Route Handlers.
  - `src/lib/supabase/middleware.ts` — Proxy client (`createServerClient` with cookie forwarding). Token refresh + route protection.
- **API Layer:** `src/lib/api.ts` — `apiFetch<T>(path, opts)` accepts optional `token` param. Injects `Authorization: Bearer` header when token provided. Unauthenticated calls (spots, sessions listing) omit token.
- **Map Discovery:** `src/components/SpotMap.tsx` renders Leaflet map with `react-leaflet-cluster` grouping spots at high zoom. Dynamically imported via `src/components/Map.tsx` using `next/dynamic` with `ssr: false` (Leaflet requires `window`). Default center `[33.3853, -119.5828]` zoom `5` (California overview). Tracks bounds on `moveend`, fetches visible spots via TanStack Query using float box query (`min_lat`, `max_lat`, `min_lng`, `max_lng`). Marker click sets `activeSpotId`. Marker icons fixed via CDN `L.icon()` (unpkg) assigned to `L.Marker.prototype.options.icon` (Next.js bundler breaks local image imports). Strict-mode mount guard (`useState` + `useEffect`) prevents Leaflet double-mount crash.
- **Session Feed:** `src/components/SessionFeed.tsx` accepts `spotId` prop, uses `useInfiniteQuery` to fetch `GET /api/sessions?spot_id=...&limit=10&cursor=...`. Renders cards (thumbnail, date, price). Clicking a card toggles inline `<Player>` for that session. "Load more" paginates via `next_cursor`. Shows "Log in to purchase" link when not authenticated.
- **Discovery Page:** `src/app/page.tsx` — split layout: map top/left, feed bottom/right. Manages `activeSpotId`, passes to both.
- **Leaflet CSS:** Imported via JS `import "leaflet/dist/leaflet.css"` in `src/app/layout.tsx` (Tailwind v4 drops `@import` in CSS files). Tile img override in `src/app/globals.css` prevents Tailwind `max-width: 100%` from distorting tiles.
- **Player:** Custom `hls.js` component wraps HTML5 `<video>`. Soft-concatenates chronologically sorted clips within a Session. Pre-buffers next clip.
- **Upload Page:** `src/app/sessions/new/page.tsx` — protected by proxy middleware. Uses `useAuth()` for JWT (no manual token input). Session creation + video upload flow.
- **Upload Hook:** `src/hooks/useVideoUpload.ts` handles R2 multipart uploads. 10 MB chunks via `File.slice`, max 3 concurrent PUTs, localStorage resume state (matches file name+size to recover after tab reload), progress reporting. Uses `apiFetch` `token` param for authenticated endpoints.


## Backend Architecture (FastAPI)

- **Framework:** FastAPI with `slowapi` rate limiting.
- **CORS:** `CORSMiddleware` added in `app/main.py`. Origins read from `CORS_ORIGINS` env var (comma-separated), defaults to `http://localhost:3000`. `allow_credentials=True`, wildcard methods/headers.
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
  - `/api/sessions/{session_id}/clips` — GET returns `stream_uid` list for ready clips in a session, ordered by `captured_at`. No auth required.
  - `/api/clips/multipart` — R2 multipart upload (initiate, presign-parts, complete). Requires auth. 5 GB file size limit. Complete endpoint triggers Stream ingest as background task.
  - `/api/webhooks/cloudflare` — Cloudflare Stream webhook. HMAC-SHA256 signature verification. Updates clip status and session thumbnail.
  - `/api/webhooks/stripe` — Stripe webhook. Signature verification via `stripe.Webhook.construct_event`. Idempotency via `stripe_events` table. Handles `checkout.session.completed` to record purchases.
  - `/api/purchases/checkout` — POST creates Stripe Checkout Session with Connect transfer_data (20% platform fee). Requires auth. Validates filmer has `stripe_account_id`.
- **Seed Script:** `scripts/seed.py` inserts approved spots (Pipeline, Lowers, Uluwatu).
