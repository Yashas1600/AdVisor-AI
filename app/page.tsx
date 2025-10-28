"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "./lib/supabaseClient";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const { data } = await supabase.auth.getSession();
      if (data.session) {
        router.push("/dashboard");
      } else {
        router.push("/signin");
      }
    };
    checkAuth();
  }, [router]);

  return (
    <div className="min-h-screen w-screen bg-black text-white flex items-center justify-center">
      <div className="text-neutral-400">Loading...</div>
    </div>
  );
}
