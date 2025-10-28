import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function POST(req: Request) {
  try {
    const body = await req.json();

    const resp = await fetch(`${BACKEND_URL}/api/analyze-ad-smart`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    }).catch((e) => ({ ok: false, status: 502, text: async () => String(e) } as any));

    if (!resp.ok) {
      const text = await (resp as any).text?.().catch(() => "")
        || "Upstream error";
      return NextResponse.json({ error: text }, { status: resp.status || 502 });
    }

    const data = await resp.json().catch(async () => ({ raw: await resp.text().catch(() => null) }));
    return NextResponse.json(data ?? null, { status: 200 });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message ?? "Proxy error" }, { status: 500 });
  }
}
