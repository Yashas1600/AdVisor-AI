import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    const file = formData.get("file");

    if (!file || typeof file === "string") {
      return NextResponse.json({ error: "file is required" }, { status: 400 });
    }

    // file is a Blob or File
    const outbound = new FormData();
    const filename = (file as any).name || "upload.bin";
    outbound.append("file", file, filename);

    const resp = await fetch("http://localhost:8000/extract", {
      method: "POST",
      body: outbound as any,
    }).catch((e) => ({ ok: false, status: 502, text: async () => String(e) } as any));

    if (!resp.ok) {
      const text = await (resp as any).text?.().catch(() => "")
        || "Upstream error";
      return NextResponse.json({ error: text }, { status: resp.status || 502 });
    }

    // Try json first, fallback to text
    const data = await resp.json().catch(async () => ({ raw: await resp.text().catch(() => null) }));
    return NextResponse.json(data ?? null, { status: 200 });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message ?? "Proxy error" }, { status: 500 });
  }
}


