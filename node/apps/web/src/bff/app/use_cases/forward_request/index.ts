import type { ImageApi } from "../../ports";
export class ForwardRequest {
  constructor(private readonly api: ImageApi) {}
  execute(path: string, request: Request) {
    return this.api.forward(path, request);
  }
}
