const BASE: string = import.meta.env.VITE_API_URL ?? "";

export type Article = {
  id: number; title: string; author: string; publisher: string; published: string; kind: string; exam: string;
  topic: string; keywords: string; perspective: string; summary: string; url: string; is_demo: boolean; bookmarked: boolean;
};
export type CompareResult = {
  mode: "demo" | "gemini" | "unavailable"; label: string; common: string[]; differences: string[]; synthesis: string;
  perspectives: { publisher: string; author: string; perspective: string; summary: string; url: string; is_demo: boolean }[];
};

export const getToken = () => localStorage.getItem("pl_token");
export const setToken = (t: string | null) => (t ? localStorage.setItem("pl_token", t) : localStorage.removeItem("pl_token"));

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const t = getToken();
  let res: Response;
  try {
    res = await fetch(BASE + path, {
      ...init,
      headers: { "Content-Type": "application/json", ...(t ? { Authorization: `Bearer ${t}` } : {}) },
    });
  } catch {
    throw new Error("Cannot reach the server. Check your connection and try again.");
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401 && t) { setToken(null); location.assign("/login"); }
    throw new Error(typeof body.detail === "string" ? body.detail : "Please check the details you entered.");
  }
  return body as T;
}
