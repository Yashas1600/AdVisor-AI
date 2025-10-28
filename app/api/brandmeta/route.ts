import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const url = new URL("http://localhost:8000/brandmeta");
    // Forward all incoming search params; default provider=openai if not supplied
    const incoming = new URL(req.url);
    const sp = incoming.searchParams;
    if (!sp.has("provider")) url.searchParams.set("provider", "openai");
    sp.forEach((v, k) => url.searchParams.set(k, v));

    const resp = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    }).catch((e) => ({ ok: false, status: 502, text: async () => String(e) } as any));

    if (!resp.ok) {
      const text = await (resp as any).text?.().catch(() => "") || "Upstream error";
      return NextResponse.json({ error: text }, { status: resp.status || 502 });
    }

    const data = await resp.json().catch(async () => ({ raw: await resp.text().catch(() => null) }));
    return NextResponse.json(data ?? null, { status: 200 });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message ?? "Proxy error" }, { status: 500 });
  }
}


