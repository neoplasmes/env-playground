import type { Job, SubmitImage } from "@/core/entities";
export interface ReadOptions {
  signal?: AbortSignal;
}
export interface JobRepo {
  list(options?: ReadOptions): Promise<Job[]>;
  create(input: SubmitImage): Promise<Job>;
}
