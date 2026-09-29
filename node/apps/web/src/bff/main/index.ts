import { ForwardRequest } from "../app/use_cases/forward_request";
import { HttpImageApi } from "../env";
export function createForwardRequest() {
  return new ForwardRequest(new HttpImageApi(process.env.IMAGE_API_URL ?? "http://127.0.0.1:8080"));
}
