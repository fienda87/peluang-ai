"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, getToken } from "../../lib/auth";

export default function SettingsPage() {
  const [auto, setAuto] = useState(true);
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState("");
  const [authed, setAuthed] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setAuthed(false);
      return;
    }
    fetch("http://localhost:8000/admin/pipeline/schedule")
      .then((r) => r.json())
      .then((d) => setAuto(d.auto_daily))
      .catch(() => {});
  }, []);

  async function toggleAuto() {
    const next = !auto;
    setAuto(next);
    await fetch("http://localhost:8000/admin/pipeline/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enable: next }),
    });
    setMsg(next ? "Auto harian: ON (07:00)" : "Auto harian: OFF");
  }

  async function runNow() {
    setRunning(true);
    setMsg("");
    try {
      await api("/admin/pipeline/run-now", { method: "POST" });
      setMsg("Pipeline jalan di background — cek hasil beberapa menit lagi.");
    } catch {
      setMsg("Gagal menjalankan.");
    } finally {
      setRunning(false);
    }
  }

  if (!authed) {
    return (
      <main className="page-shell">
        <div className="empty-state">
          <h3>Belum login.</h3>
          <p>
            <Link href="/login" style={{ color: "var(--accent)", fontWeight: 700 }}>
              Masuk dulu
            </Link>
            .
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Pengaturan</h1>
      <p className="page-sub">Kontrol pipeline data dan preferensi notifikasi.</p>

      <div className="simple-card">
        <h2 style={{ fontSize: 17, marginBottom: 8 }}>Pipeline data</h2>
        <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 16 }}>
          Crawl sumber + ekstraksi LLM. Dokumen lama otomatis dilewati — hanya
          peluang baru yang diproses.
        </p>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 14,
            padding: "12px 0",
            borderTop: "1px solid var(--line)",
          }}
        >
          <div>
            <strong style={{ fontSize: 14.5 }}>Jalankan otomatis tiap hari</strong>
            <p className="muted" style={{ fontSize: 13 }}>
              Setiap 07:00 pagi (setelah reset kuota LLM)
            </p>
          </div>
          <button
            onClick={toggleAuto}
            style={{
              minWidth: 64,
              height: 32,
              borderRadius: 999,
              border: "1px solid var(--line)",
              background: auto ? "var(--accent)" : "#e5e5e0",
              color: auto ? "#fff" : "var(--muted)",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            {auto ? "ON" : "OFF"}
          </button>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 14,
            padding: "12px 0",
            borderTop: "1px solid var(--line)",
          }}
        >
          <div>
            <strong style={{ fontSize: 14.5 }}>Jalankan sekarang</strong>
            <p className="muted" style={{ fontSize: 13 }}>
              Crawl + ekstraksi manual kapan pun mau
            </p>
          </div>
          <button className="primary-button" onClick={runNow} disabled={running}>
            {running ? "Menjalankan…" : "▶ Run now"}
          </button>
        </div>

        {msg && (
          <p style={{ marginTop: 10, color: "var(--accent)", fontSize: 13.5, fontWeight: 600 }}>
            {msg}
          </p>
        )}
      </div>
    </main>
  );
}
