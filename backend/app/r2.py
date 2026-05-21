import os
from typing import Any

import boto3
from dotenv import load_dotenv

load_dotenv()

R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.environ.get("R2_BUCKET_NAME", "")

_missing = [k for k, v in {
    "R2_ACCOUNT_ID": R2_ACCOUNT_ID,
    "R2_ACCESS_KEY_ID": R2_ACCESS_KEY_ID,
    "R2_SECRET_ACCESS_KEY": R2_SECRET_ACCESS_KEY,
    "R2_BUCKET_NAME": R2_BUCKET,
}.items() if not v]

if _missing:
    raise RuntimeError(
        f"Missing R2 env vars: {', '.join(_missing)}. "
        "Copy backend/.env.example to backend/.env and fill in Cloudflare R2 credentials."
    )

ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

r2_client: Any = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    region_name="auto",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 * 1024  # 5 GB
