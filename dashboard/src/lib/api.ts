const DEFAULT_BACKEND_HTTP = "http://127.0.0.1:8000";

function normalizeBaseUrl(url: string): string {
  return url.replace(/\/+$/, "");
}

export function getBackendHttpBase(): string {
  const configured = process.env.NEXT_PUBLIC_BACKEND_URL?.trim();
  return normalizeBaseUrl(configured || DEFAULT_BACKEND_HTTP);
}

export function getBackendWsBase(): string {
  const httpBase = getBackendHttpBase();
  if (httpBase.startsWith("https://")) {
    return httpBase.replace("https://", "wss://");
  }
  if (httpBase.startsWith("http://")) {
    return httpBase.replace("http://", "ws://");
  }
  return httpBase;
}

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getBackendHttpBase()}${normalizedPath}`;
}

export function wsUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getBackendWsBase()}${normalizedPath}`;
}
