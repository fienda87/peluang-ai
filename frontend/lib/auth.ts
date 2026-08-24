const API = "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("peluang_token");
}

export function getUser(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("peluang_user");
}

export function setAuth(token: string, userId: string) {
  localStorage.setItem("peluang_token", token);
  localStorage.setItem("peluang_user", userId);
}

export function logout() {
  localStorage.removeItem("peluang_token");
  localStorage.removeItem("peluang_user");
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}
