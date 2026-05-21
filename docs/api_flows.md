\## 1. Upload Sequence (Client -> R2 -> Stream)

1\. \*\*Init Session:\*\* JS calls `POST /api/sessions` with `spot\_id`, `start\_time`, `end\_time`, `price` (>$5). Returns `session\_id`.

2\. \*\*Read Meta:\*\* JS `mp4box.js` extracts timestamp from local file. 

3\. \*\*Get Auth:\*\* JS calls `POST /api/clips/presigned-url` providing file size and `session\_id`.

4\. \*\*FastAPI Guard:\*\* Enforces exact domain CORS policy. Generates strict Cloudflare R2 Presigned POST URL with size limits. Returns URL.

5\. \*\*Direct Upload:\*\* JS uses R2 Multipart upload API in browser to chunk and upload raw file directly to R2 bucket.

6\. \*\*Trigger Ingest:\*\* JS calls `POST /api/clips/{id}/ingest`. FastAPI returns 200 OK immediately and uses `BackgroundTasks` to send R2 HTTP link to Cloudflare Stream API. Status -> "processing".



\## 2. Cloudflare Stream Webhook Sequence

1\. \*\*Webhook Receive:\*\* Stream hits `POST /api/webhooks/cloudflare`.

2\. \*\*Status Check:\*\* If `status == ready`, update `Clips.status = "ready"`.

3\. \*\*Watermark Trigger:\*\* FastAPI `BackgroundTasks` calls Stream API to apply hard-burned watermark using Watermark UID.

4\. \*\*Thumbnail Pick:\*\* If this is the first clip in the session, extract Stream thumbnail URL, update `Sessions.thumbnail\_url`.

5\. \*\*Error Check:\*\* If Stream reports error, update `Clips.status = "failed"`. 



\## 3. Stripe Checkout Sequence

1\. \*\*Init Checkout:\*\* User clicks "Buy". JS calls `POST /api/purchases/checkout` with `session\_id`.

2\. \*\*Split Pay:\*\* FastAPI creates Stripe Checkout Session. Maps `destination` to filmer's `stripe\_account\_id`. Sets app platform fee.

3\. \*\*Webhook Receive:\*\* Stripe hits `POST /api/webhooks/stripe`.

4\. \*\*Idempotency Check:\*\* FastAPI verifies `Stripe-Signature`. Checks if `StripeEvents.id` exists. If yes, ignore. If no, insert event, write `Purchases` row.



\## 4. Paid Download Sequence

1\. \*\*Request DL:\*\* Buyer JS calls `GET /api/sessions/{session\_id}/download-links`.

2\. \*\*Verify:\*\* FastAPI checks `Purchases` table for `user\_id` + `session\_id`.

3\. \*\*Generate:\*\* FastAPI loops through all raw clips in session. Generates short-lived (1 hour) R2 Presigned GET URLs. Returns array.

4\. \*\*Client Execute:\*\* Frontend sequential JS download manager fetches files local machine.



\## 5. Cron TTL Deletion

1\. \*\*Trigger:\*\* Railway daily scheduler hits protected internal route or runs python script.

2\. \*\*Find:\*\* Query `Clips` where `created\_at` > 30 days and `is\_deleted` == False.

3\. \*\*Cleanup:\*\* Fire Cloudflare Stream API DELETE. (R2 deletes raw file automatically via Bucket Lifecycle rule).

4\. \*\*Update:\*\* Mark `is\_deleted = True`. Keep DB rows for receipt history.

