import { createForwardRequest } from "@/bff/main";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
async function handler(request: Request, { params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await params;
  if (
    path.length > 2 ||
    (path[0] && !/^[0-9a-f-]{36}$/.test(path[0])) ||
    (path[1] && path[1] !== "result")
  ) {
    return Response.json({ error: "Not found" }, { status: 404 });
  }
  if (request.method === "POST") {
    if (path.length) return Response.json({ error: "Method not allowed" }, { status: 405 });
    const origin = request.headers.get("origin");
    if (origin && origin !== new URL(request.url).origin && origin !== process.env.PUBLIC_ORIGIN) {
      return Response.json({ error: "Invalid origin" }, { status: 403 });
    }
  }
  try {
    return await createForwardRequest().execute(
      "/v1/jobs" + (path.length ? "/" + path.join("/") : "") + new URL(request.url).search,
      request,
    );
  } catch (error) {
    if (error instanceof RangeError)
      return Response.json({ error: error.message }, { status: 413 });

    return Response.json({ error: "Сервис обработки временно недоступен" }, { status: 502 });
  }
}
export { handler as GET, handler as POST };
