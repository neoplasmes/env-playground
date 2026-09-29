import type { EntityRef } from "./entity_ref";
export interface Job {
  readonly ref: EntityRef;
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  width: number;
  height: number;
  format: "png" | "jpeg" | "webp";
  error: string | null;
  createdAt: number;
}
export interface SubmitImage {
  image: Blob;
  width: number;
  height: number;
  format: Job["format"];
  idempotencyKey: string;
}
