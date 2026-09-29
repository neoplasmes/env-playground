import type { JobRepo } from "@/app/ports";
import type { EntityRef, SubmitImage } from "@/core/entities";
export class CreateJob {
  constructor(private readonly repo: JobRepo) {}
  execute(input: SubmitImage) {
    return this.repo.create(input);
  }
  writes(): EntityRef[] {
    return ["job"];
  }
}
