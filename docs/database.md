## SQLModel Schema Definitions


### Users

- `id`: UUID (Primary Key, matches Supabase Auth ID)
- `email`: String (Unique)
- `stripe_account_id`: String (Nullable, for Connect payout)
- `created_at`: UTC Timestamp


### Spots

- `id`: UUID (Primary Key)
- `name`: String
- `lat`: Float (Index for bounding box query)
- `lng`: Float (Index for bounding box query)
- `timezone`: String (e.g., "America/Los_Angeles")
- `is_approved`: Boolean (Admin approval for user-suggested spots)


### Sessions

- `id`: UUID (Primary Key)
- `spot_id`: UUID (Foreign Key -> Spots, ON DELETE CASCADE)
- `filmer_id`: UUID (Foreign Key -> Users, ON DELETE CASCADE)
- `start_time`: UTC Timestamp (Approximate start)
- `end_time`: UTC Timestamp (Approximate end)
- `price`: Integer (Cents, minimum $500 enforced at API layer)
- `thumbnail_url`: String (Nullable, auto-populated from first clip)
- `created_at`: UTC Timestamp


### Clips

- `id`: UUID (Primary Key)
- `session_id`: UUID (Foreign Key -> Sessions, ON DELETE CASCADE, Indexed)
- `captured_at`: UTC Timestamp (Extracted from JS mp4box.js, used for internal chronological sort, Indexed)
- `r2_raw_key`: String (Path in R2 bucket)
- `stream_uid`: String (Nullable, Cloudflare Stream ID)
- `status`: String (Enum: "uploading", "uploaded", "processing", "ready", "failed")
- `is_deleted`: Boolean (Default False, set to True by 30-day cron script)


### Purchases

- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> Users, ON DELETE CASCADE)
- `session_id`: UUID (Foreign Key -> Sessions, ON DELETE CASCADE)
- `stripe_session_id`: String (Unique)
- `amount_cents`: Integer
- `created_at`: UTC Timestamp


### StripeEvents (Idempotency)

- `id`: String (Primary Key, Stripe Event ID)
- `type`: String
- `processed_at`: UTC Timestamp
