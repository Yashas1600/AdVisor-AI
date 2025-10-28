"use client";

import { useState } from "react";
import { supabase } from "../lib/supabaseClient";
import Link from "next/link";

export default function SignUpPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showVerificationMessage, setShowVerificationMessage] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      const { error: err } = await supabase.auth.signUp({ email, password });
      if (err) throw err;
      setShowVerificationMessage(true);
    } catch (e: any) {
      setError(e?.message ?? "Authentication error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-black text-white flex items-center justify-center">
      {/* Verification Email Popup */}
      {showVerificationMessage && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="w-[420px] max-w-[92vw] rounded-2xl border border-neutral-800 bg-neutral-950 p-6 shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
                <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold">Verify your email</h3>
            </div>
            <p className="text-neutral-300 mb-2">
              We&apos;ve sent a verification link to:
            </p>
            <p className="text-white font-medium mb-4 bg-neutral-900 px-3 py-2 rounded-md border border-neutral-800">
              {email}
            </p>
            <p className="text-sm text-neutral-400 mb-6">
              Click the link in the email to verify your account and start using AdVisor.
            </p>
            <Link href="/signin">
              <button className="w-full rounded-md bg-neutral-100 text-black px-4 py-2 hover:bg-neutral-200 transition-colors">
                Go to Sign In
              </button>
            </Link>
          </div>
        </div>
      )}

      {/* Sign Up Form */}
      <div className="w-[380px] max-w-[92vw] rounded-2xl border border-neutral-800 bg-neutral-950/95 p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-neutral-200 text-neutral-900 font-bold flex items-center justify-center">A</div>
            <span className="text-sm text-neutral-400">AdVisor</span>
          </div>
          <Link href="/signin" className="text-xs text-neutral-400 hover:text-neutral-200">
            Have an account? Sign in
          </Link>
        </div>

        <h3 className="mt-4 text-xl font-semibold">Create your account</h3>

        <div className="mt-4 space-y-3">
          <div>
            <label className="text-sm text-neutral-400">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 outline-none focus:border-neutral-600"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="text-sm text-neutral-400">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 outline-none focus:border-neutral-600"
              placeholder="••••••••"
            />
          </div>
          {error && <div className="text-sm text-red-400">{error}</div>}
          <button
            className="mt-2 w-full rounded-md bg-neutral-100 text-black px-4 py-2 disabled:opacity-50"
            disabled={loading || !email || !password}
            onClick={handleSubmit}
          >
            {loading ? "Please wait..." : "Sign up"}
          </button>
        </div>
      </div>
    </div>
  );
}
