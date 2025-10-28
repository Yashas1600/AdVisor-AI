"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../lib/supabaseClient";
import Link from "next/link";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      const { error: err } = await supabase.auth.signInWithPassword({ email, password });
      if (err) throw err;
      router.push("/dashboard");
    } catch (e: any) {
      setError(e?.message ?? "Authentication error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-black text-white flex items-center justify-center">
      <div className="w-[380px] max-w-[92vw] rounded-2xl border border-neutral-800 bg-neutral-950/95 p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-neutral-200 text-neutral-900 font-bold flex items-center justify-center">A</div>
            <span className="text-sm text-neutral-400">AdVisor</span>
          </div>
          <Link href="/signup" className="text-xs text-neutral-400 hover:text-neutral-200">
            Create account
          </Link>
        </div>

        <h3 className="mt-4 text-xl font-semibold">Sign in</h3>

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
            {loading ? "Please wait..." : "Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}
