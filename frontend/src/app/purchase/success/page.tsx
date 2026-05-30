"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";

function SuccessContent() {
  const params = useSearchParams();
  const sessionId = params.get("session_id");

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="max-w-md rounded-lg border bg-card p-8 text-center shadow-sm">
        <h1 className="text-2xl font-bold">Purchase Confirmed</h1>
        <p className="mt-2 text-muted-foreground">
          Your payment was successful. You can now download your clips.
        </p>
        {sessionId && (
          <p className="mt-1 text-xs text-muted-foreground">
            Checkout ID: {sessionId}
          </p>
        )}
        <Link
          href="/purchases"
          className="mt-6 inline-block rounded bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          View My Purchases
        </Link>
      </div>
    </div>
  );
}

export default function PurchaseSuccessPage() {
  return (
    <Suspense>
      <SuccessContent />
    </Suspense>
  );
}
