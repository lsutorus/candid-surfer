"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import LoginForm from "@/components/LoginForm";

function LoginFormWrapper() {
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") ?? "/";
  return <LoginForm redirectTo={redirectTo} />;
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginFormWrapper />
    </Suspense>
  );
}
