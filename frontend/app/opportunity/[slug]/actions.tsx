"use client";

import { useState } from "react";

const API = "http://localhost:8000";

export default function OpportunityActions({ slug }: { slug: string }) {
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function act(eventType: "save" | "apply") {
    const token = localStorage.getItem("peluang_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    setBusy(true);
    try {
      // cari id opportunity by slug lalu kirim event
      const search = await fetch(
        `http://localhost:8000/opportunities?q=${encodeURIComponent(slug)}&limit=5`
      ).then((r) => r.json());
      const opp = search.find((o: { slug: string }) => o.slug === slug);
      if (!opp) throw new Error("not found");

      await fetch(`${API}/events`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          event_type: eventType,
          opportunity_id: opp.id,
        }),
      });
      setStatus(eventType === "save" ? "Tersimpan ✓" : "Tercatat sebagai dilamar ✓");
    } catch {
      setStatus("Gagal — coba login ulang.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="action-row">
      <button className="primary-button" disabled={busy} onClick={() => act("save")}>
        Simpan
      </button>
      <button
        className="secondary-button"
        disabled={busy}
        onClick={() => act("apply")}
      >
        Tandai Dilamar
      </button>
      {status && (
        <span style={{ alignSelf: "center", fontSize: 13.5, color: "var(--accent)", fontWeight: 600 }}>
          {status}
        </span>
      )}
    </div>
  );
}
