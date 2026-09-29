export class HttpTransport {
  async request(path: string, init: RequestInit = {}): Promise<unknown> {
    const response = await fetch(path, { ...init, cache: "no-store" });
    if (!response.ok) {
      const body = await response.json().catch(() => null);

      throw new Error(body?.error ?? `Request failed (${response.status})`);
    }

    return response.json();
  }
}
