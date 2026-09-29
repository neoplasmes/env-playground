import type { ImageApi } from "../app/ports";
export class HttpImageApi implements ImageApi {
  constructor(private readonly base: string) {}
  async forward(path: string, request: Request) {
    const headers = new Headers();
    headers.set("Content-Type", "application/octet-stream");
    const key = request.headers.get("Idempotency-Key");
    if (key) headers.set("Idempotency-Key", key);
    const body = request.method === "POST" ? await readBounded(request) : undefined;
    const upstream = await fetch(this.base + path, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    const outgoing = new Headers({
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    });
    for (const name of ["Content-Type", "Content-Disposition"]) {
      const value = upstream.headers.get(name);
      if (value) outgoing.set(name, value);
    }

    return new Response(upstream.body, { status: upstream.status, headers: outgoing });
  }
}
async function readBounded(request: Request): Promise<ArrayBuffer> {
  const reader = request.body?.getReader();
  if (!reader) throw new Error("Empty upload");
  const chunks: Uint8Array[] = [];
  let length = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > 10 * 1024 * 1024) {
        await reader.cancel();

        throw new RangeError("Maximum upload size is 10 MiB");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const output = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.byteLength;
  }

  return output.buffer;
}
