"use client";

import Link from "next/link";

export default function PurchaseCancelPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="max-w-md rounded-lg border bg-card p-8 text-center shadow-sm">
        <h1 className="text-2xl font-bold">Purchase Cancelled</h1>
        <p className="mt-2 text-muted-foreground">
          Your checkout was cancelled. You have not been charged.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block rounded border px-6 py-2 text-sm font-medium hover:bg-accent"
        >
          Back to Map
        </Link>
      </div>
    </div>
  );
}
