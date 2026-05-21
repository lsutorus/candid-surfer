## 1. Upload Sequence (Client -> R2 -> Stream)

1. **Init Session:** JS calls `POST /api/sessions` with `spot_id`, `start_time`, `end_time`, `price` (>$5). Returns `session_id`.

2. **Read Meta:** JS `mp4box.js` extracts timestamp from local file.

3. **Init Multipart:** JS calls `POST /api/clips/multipart/initiate` with `session_id`, `filename`, `file_size`, `captured_at`. Returns `clip_id`, `upload_id`, `key`.

4. **Presign Parts:** JS calls `POST /api/clips/multipart/presign-parts` with `key`, `upload_id`, `part_numbers`. Returns presigned PUT URLs per part (1hr TTL).

5. **Direct Upload:** JS `File.slice` splits file into 10 MB chunks. Max 3 concurrent PUT requests to presigned R2 URLs. Each PUT response provides `ETag`. Progress saved to `localStorage` keyed by `sessionId:fileName:fileSize`. On tab reload, hook detects matching file and resumes (re-initiates since ETags aren't persisted). When all parts done, calls `POST /api/clips/multipart/complete` with `clip_id`, `upload_id`, `key`, `parts` (PartNumber + ETag). Updates clip status to "uploaded".

6. **Trigger Ingest:** JS calls `POST /api/clips/{id}/ingest`. FastAPI returns 200 OK immediately and uses `BackgroundTasks` to send R2 HTTP link to Cloudflare Stream API. Status -> "processing".


## 2. Cloudflare Stream Webhook Sequence

1. **Webhook Receive:** Stream hits `POST /api/webhooks/cloudflare`.

2. **Status Check:** If `status == ready`, update `Clips.status = "ready"`.

3. **Watermark Trigger:** FastAPI `BackgroundTasks` calls Stream API to apply hard-burned watermark using Watermark UID.

4. **Thumbnail Pick:** If this is the first clip in the session, extract Stream thumbnail URL, update `Sessions.thumbnail_url`.

5. **Error Check:** If Stream reports error, update `Clips.status = "failed"`.



## 3. Stripe Checkout Sequence

1. **Init Checkout:** User clicks "Buy". JS calls `POST /api/purchases/checkout` with `session_id`.

2. **Split Pay:** FastAPI creates Stripe Checkout Session. Maps `destination` to filmer's `stripe_account_id`. Sets app platform fee.

3. **Webhook Receive:** Stripe hits `POST /api/webhooks/stripe`.

4. **Idempotency Check:** FastAPI verifies `Stripe-Signature`. Checks if `StripeEvents.id` exists. If yes, ignore. If no, insert event, write `Purchases` row.



## 4. Paid Download Sequence

1. **Request DL:** Buyer JS calls `GET /api/sessions/{session_id}/download-links`.

2. **Verify:** FastAPI checks `Purchases` table for `user_id` + `session_id`.

3. **Generate:** FastAPI loops through all raw clips in session. Generates short-lived (1 hour) R2 Presigned GET URLs. Returns array.

4. **Client Execute:** Frontend sequential JS download manager fetches files local machine.



## 5. Cron TTL Deletion

1. **Trigger:** Railway daily scheduler hits protected internal route or runs python script.

2. **Find:** Query `Clips` where `created_at` > 30 days and `is_deleted` == False.

3. **Cleanup:** Fire Cloudflare Stream API DELETE. (R2 deletes raw file automatically via Bucket Lifecycle rule).

4. **Update:** Mark `is_deleted = True`. Keep DB rows for receipt history.
