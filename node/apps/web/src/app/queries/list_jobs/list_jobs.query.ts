import type { JobRepo, ReadOptions } from "@/app/ports";
import type { EntityRef } from "@/core/entities";
export class ListJobs {
  readonly name = "list_jobs";
  constructor(private readonly repo: JobRepo) {}
  execute(_input: undefined, options?: ReadOptions) {
    return this.repo.list(options);
  }
  reads(): EntityRef[] {
    return ["job"];
  }
}
