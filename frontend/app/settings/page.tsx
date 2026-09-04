"use client";
import { API_URL } from "../../lib/api";

import { useEffect, useState } from "react";

export default function SettingsPage() {
  const [auto, setAuto] = useState(true);
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState("");

  const API = API_URL;

  useEffect(() => {
    fetch(`${API}/admin/pipeline/schedule`)
      .then((r) => r.json())
      .then((d) => setAuto(d.auto_daily))
      .catch(() => {});
  }, []);

  async function toggleAuto() {
    const next = !auto;
    setAuto(next);
    await fetch(`${API}/admin/pipeline/schedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enable: next }),
    }).catch(() => {});
    setMsg(next ? "Auto harian: ON (07:00)" : "Auto harian: OFF");
  }

  async function runNow() {
    setRunning(true);
    setMsg("");
    try {
      await fetch(`${API}/admin/pipeline/run-now`, { method: "POST" });
      setMsg("Pipeline jalan di background — cek hasil beberapa menit lagi.");
    } catch {
      setMsg("Gagal menjalankan.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Pengaturan</h1>
      <p className="page-sub">Kontrol pipeline data dan preferensi notifikasi.</p>

      <div className="simple-card">
        <h2 style={{ fontSize: 17, marginBottom: 8 }}>Pipeline data</h2>
        <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 16 }}>
          Crawl sumber + ekstraksi LLM lokal. Dokumen lama otomatis dilewati —
          hanya peluang baru yang diproses.
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
            <p style={{ fontSize: 13, color: "var(--muted)" }}>
              Setiap 07:00 pagi
            </p>
          </div>
          <button
            onClick={toggleAuto}
            style={{
              minWidth: 64,
              height: 32,
              borderRadius: 999,
              border: "1px solid var(--line)",
              background: auto ? "var(--accent)" : "#1c2530",
              color: auto ? "#06222b" : "var(--muted)",
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
            <p style={{ fontSize: 13, color: "var(--muted)" }}>
              Crawl + ekstraksi manual kapan pun
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
