# Project Rules
- Runtime: PowerShell 7.x (pwsh)
- Do not use legacy WMI cmdlets (use CIM instead).
- Use forward slashes `/` for paths to prevent escape-character bugs during CLI tool execution.
- Use `uv` (not pip) for Python package management in backend venv.

## System constitution: Candid Surfer
This document defines core rules. Review `/docs/architecture.md`, `/docs/database.md`, and `/docs/api_flows.md` before planning tasks.

### Core Stack
- Frontend: Next.js (App Router), Tailwind CSS, shadcn/ui, TanStack Query, Leaflet (via `react-leaflet-cluster`), `hls.js` (custom soft-concat player).
- Backend: FastAPI, SQLModel (Pydantic + SQLAlchemy), Alembic.
- Database: Supabase PostgreSQL (accessed via Supavisor Transaction Pool URL).
- Storage/Video: Cloudflare R2 (Raw 4K), Cloudflare Stream (HLS, watermarking, thumbnails).
- Payments: Stripe Connect (Split payments), Stripe Hosted Checkout.
- Infrastructure: Vercel (Frontend), Railway (Backend). Sentry (Error tracking).

### Strict Anti-Patterns (NEVER DO THESE)
- **Do not** process video via FFmpeg on the backend. Always use Cloudflare Stream API/Webhooks.
- **Do not** use PostGIS. Use standard PostgreSQL float math for map bounding box queries.
- **Do not** enable SSR for Leaflet map components. Always use `next/dynamic` with `ssr: false`.
- **Do not** proxy large video uploads/downloads through FastAPI. Always use browser-to-R2 presigned URLs.
- **Do not** use Supabase API for JWT verification in FastAPI. Verify tokens via JWKS public key fetch (ES256), not shared secret.
- **Do not** build custom user roles (e.g., Filmer vs. Surfer table). Use a single unified `Users` table.
- **Do not** poll for video status. Rely strictly on Cloudflare Stream webhooks.
- **Do not** guess strings for file update tools. Always read exact lines first, copy exact text, then replace. If edit fails, rewrite entire file.

### Workflow Directives
- **Updating Docs:** Update the `/docs` files at the end of sessions to reflect structural changes.
- **State Check:** Before implementing large features, read the relevant `/docs/` file to maintain alignment.
- **Roadmap:** Read `docs/roadmap.md` before starting work to find next pending phase. Mark items as `[x]` completed after implementation.

## Agent skills

### Issue tracker
Issues live in GitHub (lsutorus/candid-surfer). Uses `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels
Default vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs
Single-context — one CONTEXT.md + docs/adr/ at repo root. See `docs/agents/domain.md`.