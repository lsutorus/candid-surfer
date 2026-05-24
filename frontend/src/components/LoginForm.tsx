"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface LoginFormProps {
  redirectTo?: string;
}

const PASSWORD_HINT = "6+ chars, 1 uppercase, 1 number";

function validatePassword(p: string): string | null {
  if (p.length < 6) return "Password must be at least 6 characters";
  if (!/[A-Z]/.test(p)) return "Password needs at least one uppercase letter";
  if (!/[0-9]/.test(p)) return "Password needs at least one number";
  return null;
}

function PasswordInput({
  value,
  onChange,
  id,
}: {
  value: string;
  onChange: (v: string) => void;
  id: string;
}) {
  const [show, setShow] = useState(false);

  return (
    <div className="relative">
      <input
        id={id}
        type={show ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        minLength={6}
        className="w-full rounded border p-2 pr-10"
      />
      <button
        type="button"
        onClick={() => setShow(!show)}
        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-zinc-500 hover:text-zinc-700"
        aria-label={show ? "Hide password" : "Show password"}
      >
        {show ? (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
            <path fillRule="evenodd" d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.733-1.733C18.205 13.802 19.25 12.51 19.25 11c0-2.5-3.5-5.5-9.25-5.5-1.56 0-2.97.24-4.19.64L3.28 2.22zM7.53 9.59l3.88 3.88a2.5 2.5 0 01-3.88-3.88zM10 15.5c-5.75 0-9.25-3-9.25-5.5 0-1.33.86-2.74 2.46-3.88L5.1 8.01A4.5 4.5 0 009.99 13.5c.72 0 1.4-.17 2.02-.47l1.65 1.65c-1.16.38-2.4.82-3.66.82z" clipRule="evenodd" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
            <path d="M10 12.5a2.5 2.5 0 002.5-2.5c0-.47-.13-.91-.36-1.29l-3.43 3.43c.38.23.82.36 1.29.36z" />
            <path fillRule="evenodd" d="M.75 10c1.75-3.5 5.25-5.5 9.25-5.5s7.5 2 9.25 5.5c-1.75 3.5-5.25 5.5-9.25 5.5S2.5 13.5.75 10zm4.76 2.24l1.65-1.65A4.5 4.5 0 0113.59 6.1l1.65-1.65C13.75 3.8 12.01 3.25 10 3.25 4.25 3.25.75 7 .75 9.5c0 1.33.86 2.74 2.46 3.88l2.3-1.14z" clipRule="evenodd" />
          </svg>
        )}
      </button>
    </div>
  );
}

export default function LoginForm({ redirectTo }: LoginFormProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const supabase = createClient();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (!isLogin) {
      const pwError = validatePassword(password);
      if (pwError) {
        setError(pwError);
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match");
        return;
      }
    }

    setLoading(true);

    if (isLogin) {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) {
        setError(error.message);
      } else if (redirectTo) {
        window.location.href = redirectTo;
      }
    } else {
      const { error } = await supabase.auth.signUp({ email, password });
      if (error) {
        setError(error.message);
      } else {
        setMessage("Check your email for a confirmation link.");
      }
    }

    setLoading(false);
  }

  return (
    <div className="flex flex-1 items-center justify-center p-4">
      <form
        onSubmit={handleSubmit}
        className="flex w-full max-w-sm flex-col gap-4"
      >
        <h1 className="text-2xl font-semibold">
          {isLogin ? "Log in" : "Sign up"}
        </h1>

        <label className="flex flex-col gap-1">
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="rounded border p-2"
          />
        </label>

        <label className="flex flex-col gap-1">
          Password
          <PasswordInput value={password} onChange={setPassword} id="password" />
          {!isLogin && (
            <span className="text-xs text-zinc-500">{PASSWORD_HINT}</span>
          )}
        </label>

        {!isLogin && (
          <label className="flex flex-col gap-1">
            Verify Password
            <PasswordInput
              value={confirmPassword}
              onChange={setConfirmPassword}
              id="confirm-password"
            />
          </label>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded bg-black p-2 text-white hover:bg-zinc-800 disabled:opacity-50"
        >
          {loading ? "Loading..." : isLogin ? "Log in" : "Sign up"}
        </button>

        {error && <p className="text-red-600">{error}</p>}
        {message && <p className="text-green-600">{message}</p>}

        <button
          type="button"
          onClick={() => {
            setIsLogin(!isLogin);
            setError(null);
            setMessage(null);
            setConfirmPassword("");
          }}
          className="text-sm text-zinc-600 underline"
        >
          {isLogin
            ? "Don't have an account? Sign up"
            : "Already have an account? Log in"}
        </button>
      </form>
    </div>
  );
}
