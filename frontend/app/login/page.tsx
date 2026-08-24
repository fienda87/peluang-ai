"use client";

import { useState } from "react";
import { setAuth, api } from "../../lib/auth";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "login") {
        const r = await api<{ access_token: string; user_id: string }>("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        setAuth(r.access_token, r.user_id);
      } else {
        const r = await api<{ access_token: string; user_id: string }>("/auth/register", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        setAuth(r.access_token, r.user_id);
      }
      window.location.href = "/";
    } catch {
      setError(
        mode === "login"
          ? "Email atau password salah."
          : "Registrasi gagal — email mungkin sudah dipakai."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page-shell" style={{ maxWidth: 460 }}>
      <a className="back-link" href="/">← Beranda</a>
      <h1>{mode === "login" ? "Masuk" : "Daftar"}</h1>
      <p className="page-sub">
        {mode === "login"
          ? "Masuk untuk melihat rekomendasi personal."
          : "Buat akun untuk menyimpan dan melacak peluang."}
      </p>

      <form className="simple-card" onSubmit={submit} style={{ display: "grid", gap: 14 }}>
        <label style={{ display: "grid", gap: 6, fontSize: 14 }}>
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="search-form input"
            style={{
              height: 46, padding: "0 14px", border: "1px solid var(--line)",
              borderRadius: 10, fontSize: 15,
            }}
          />
        </label>
        <label style={{ display: "grid", gap: 6, fontSize: 14 }}>
          Password
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              height: 46, padding: "0 14px", border: "1px solid var(--line)",
              borderRadius: 10, fontSize: 15,
            }}
          />
        </label>

        {error && (
          <p style={{ color: "#b91c1c", fontSize: 13.5 }}>{error}</p>
        )}

        <button className="primary-button" type="submit" disabled={busy}>
          {busy ? "Memproses…" : mode === "login" ? "Masuk" : "Daftar"}
        </button>

        <p style={{ fontSize: 13.5, color: "var(--muted)" }}>
          {mode === "login" ? "Belum punya akun? " : "Sudah punya akun? "}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              setMode(mode === "login" ? "register" : "login");
              setError("");
            }}
            style={{ color: "var(--accent)", fontWeight: 700 }}
          >
            {mode === "login" ? "Daftar" : "Masuk"}
          </a>
        </p>
      </form>
    </main>
  );
}
