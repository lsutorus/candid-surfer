## Infrastructure Overview

- **Vercel:** Hosts Next.js client. Connects to FastAPI backend via REST.
- **Railway:** Hosts FastAPI Docker container. Runs web server and daily cron jobs.
- **Supabase:** Managed PostgreSQL DB (accessed via Supavisor Transaction Pool URL, port 6543). Auth provider.
- **Cloudflare:**
  - R2: Holds raw video uploads (presigned POST ingest, presigned GET egress). 30-day bucket lifecycle auto-delete rule.
  - Stream: Holds HLS encode, hard-burned watermarks. Webhook fires to Railway.
- **Stripe:** Connect accounts for direct filmer payout. Hosted checkout sessions for purchases.


## Frontend Architecture (Next.js)

- **Framework:** Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui.
- **State Management:** TanStack Query handles all API fetching, caching, and cursor-based infinite scrolling.
- **Map Discovery:** `react-leaflet-cluster` groups spots at high zoom. Uses float box bounds query (`min_lat`, `max_lat`, `min_lng`, `max_lng`) to fetch visible spots.
- **Player:** Custom `hls.js` component wraps HTML5 `<video>`. Soft-concatenates chronologically sorted clips within a Session. Pre-buffers next clip.


## Backend Architecture (FastAPI)

- **Framework:** FastAPI with `slowapi` rate limiting.
- **ORM:** SQLModel handles both API validation schemas and DB models. Alembic handles migrations.
- **Auth:** `HTTPBearer` extracts Bearer token, `python-jose` decodes JWT locally using `SUPABASE_JWT_SECRET`. Auto-upserts local `users` row on first verified request (id=JWT sub, email=JWT email).
- **Database:** Supabase PostgreSQL via psycopg3. `postgresql://` URLs auto-rewritten to `postgresql+psycopg://`.
- **Env Loading:** `python-dotenv` in `app/db.py`, `app/auth.py`, and `alembic/env.py` loads `.env` before reading env vars. Missing critical vars raise `RuntimeError` with setup instructions.
- **Async Processing:** FastAPI `BackgroundTasks` used for non-blocking outbound API calls (e.g., triggering Cloudflare Stream ingest after R2 upload).
- **Routers:** `/api/sessions` — POST creates session, requires auth, enforces $5 minimum price.
- **Seed Script:** `scripts/seed.py` inserts approved spots (Pipeline, Lowers, Uluwatu).
