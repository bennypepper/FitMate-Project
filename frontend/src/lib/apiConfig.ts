/**
 * apiConfig.ts: Centralized API base URL resolver.
 *
 * Automatically routes requests to local backend (http://127.0.0.1:8000)
 * when running locally in development, and to Hugging Face Spaces in production.
 */

export function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
  }

  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://127.0.0.1:8000";
    }
  }

  return "https://benedictpepper-fitmate-api.hf.space";
}
