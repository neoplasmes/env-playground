import { z } from "zod";
import type { JobRepo, ReadOptions } from "@/app/ports";
import type { Job, SubmitImage } from "@/core/entities";
import type { HttpTransport } from "@/env/transport";
const schema = z.object({
  id: z.string(),
  status: z.enum(["queued", "running", "succeeded", "failed"]),
  width: z.number(),
  height: z.number(),
  format: z.enum(["png", "jpeg", "webp"]),
  error: z.string().nullable(),
  created_at: z.number(),
});
function map(value: z.infer<typeof schema>): Job {
  return {
    ref: `job:${value.id}`,
    id: value.id,
    status: value.status,
    width: value.width,
    height: value.height,
    format: value.format,
    error: value.error,
    createdAt: value.created_at,
  };
}
export class TransportJobRepo implements JobRepo {
  constructor(private readonly http: HttpTransport) {}
  async list(options?: ReadOptions) {
    return schema
      .array()
      .parse(await this.http.request("/api/jobs", { signal: options?.signal }))
      .map(map);
  }
  async create(input: SubmitImage) {
    const query = new URLSearchParams({
      width: String(input.width),
      height: String(input.height),
      format: input.format,
    });

    return map(
      schema.parse(
        await this.http.request(`/api/jobs?${query}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/octet-stream",
            "Idempotency-Key": input.idempotencyKey,
          },
          body: input.image,
        }),
      ),
    );
  }
}
