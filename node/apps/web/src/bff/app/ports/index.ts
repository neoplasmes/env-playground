export interface ImageApi {
  forward(path: string, request: Request): Promise<Response>;
}
