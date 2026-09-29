import { describe, expect, it } from "vitest";
import { EntityStore } from "@/env/cache/entity_store";
import type { Job } from "@/core/entities";
const job: Job = {
  ref: "job:1",
  id: "1",
  status: "queued",
  width: 10,
  height: 10,
  format: "png",
  error: null,
  createdAt: 1,
};
describe("EntityStore", () => {
  it("preserves values omitted from partial reads and unchanged references", () => {
    const store = new EntityStore();
    store.upsert(job.ref, job);
    const first = store.get(job.ref);
    store.upsert(job.ref, { width: 10, error: undefined });
    expect(store.get(job.ref)).toBe(first);
    store.upsert(job.ref, { error: "bad" });
    store.upsert(job.ref, { error: null });
    expect(store.get(job.ref)?.error).toBeNull();
  });
  it("retains server updates underneath optimistic layers", () => {
    const store = new EntityStore();
    store.upsert(job.ref, job);
    const layer = store.begin();
    layer.apply([{ ref: job.ref, patch: { status: "running" } }]);
    store.upsert(job.ref, { status: "succeeded" });
    expect(store.get(job.ref)?.status).toBe("running");
    layer.discard();
    expect(store.get(job.ref)?.status).toBe("succeeded");
  });
  it("collects unreferenced entities but retains optimistic references", () => {
    const store = new EntityStore();
    store.upsert(job.ref, job);
    const layer = store.begin();
    layer.apply([{ ref: job.ref, patch: { status: "running" } }]);
    store.collect(new Set());
    expect(store.get(job.ref)).toBeDefined();
    layer.discard();
    store.collect(new Set());
    expect(store.get(job.ref)).toBeUndefined();
  });
});
