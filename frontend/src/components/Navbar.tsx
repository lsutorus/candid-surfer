"use client";

import { useAuth } from "@/components/AuthProvider";
import { createClient } from "@/lib/supabase/client";

export default function Navbar() {
  const { user, loading } = useAuth();

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/";
  }

  return (
    <nav className="flex items-center justify-between border-b px-4 py-2">
      <a href="/" className="text-lg font-semibold">
        Candid Surfer
      </a>
      <div className="flex items-center gap-3">
        {loading ? null : user ? (
          <>
            <a
              href="/sessions/new"
              className="text-sm text-zinc-600 hover:text-zinc-900"
            >
              Upload
            </a>
            <button
              onClick={handleLogout}
              className="text-sm text-zinc-600 hover:text-zinc-900"
            >
              Log out
            </button>
          </>
        ) : (
          <a
            href="/auth/login"
            className="text-sm text-zinc-600 hover:text-zinc-900"
          >
            Log in
          </a>
        )}
      </div>
    </nav>
  );
}
