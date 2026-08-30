"use client";

import { useState } from "react";

type Profile = {
  education_level?: string;
  major?: string;
  university?: string;
  graduation_year?: number;
  cgpa?: number;
  location?: string;
  skills?: string[];
  interests?: string[];
};

const FIELDS: Array<{ key: keyof Profile; label: string; type?: string }> = [
  { key: "education_level", label: "Jenjang pendidikan" },
  { key: "major", label: "Jurusan" },
  { key: "university", label: "Universitas" },
  { key: "graduation_year", label: "Tahun lulus", type: "number" },
  { key: "cgpa", label: "IPK", type: "number" },
  { key: "location", label: "Domisili" },
];

export default function ProfileForm({ initial }: { initial: Profile | null }) {
  const [profile, setProfile] = useState<Profile>(initial ?? {});
  const [skills, setSkills] = useState((initial?.skills || []).join(", "));
  const [interests, setInterests] = useState((initial?.interests || []).join(", "));
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [tgUrl, setTgUrl] = useState<string | null>(null);

  async function save() {
    setBusy(true);
    try {
      await fetch("http://localhost:8000/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...profile,
          graduation_year: profile.graduation_year
            ? Number(profile.graduation_year)
            : undefined,
          cgpa: profile.cgpa ? Number(profile.cgpa) : undefined,
          skills: skills.split(",").map((s) => s.trim()).filter(Boolean),
          interests: interests.split(",").map((s) => s.trim()).filter(Boolean),
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally {
      setBusy(false);
    }
  }

  const inputStyle = {
    height: 44,
    padding: "0 12px",
    border: "1px solid var(--line)",
    borderRadius: 10,
    fontSize: 14,
    width: "100%",
    background: "var(--surface)",
    color: "var(--ink)",
  };

  return (
    <form
      className="simple-card"
      onSubmit={(e) => {
        e.preventDefault();
        save();
      }}
      style={{ display: "grid", gap: 16 }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 14,
        }}
      >
        {FIELDS.map(({ key, label, type }) => (
          <label key={key} style={{ display: "grid", gap: 6, fontSize: 13.5 }}>
            {label}
            <input
              type={type || "text"}
              value={(profile[key] as string | number | undefined) ?? ""}
              onChange={(e) =>
                setProfile({ ...profile, [key]: e.target.value || undefined })
              }
              style={inputStyle}
            />
          </label>
        ))}
      </div>

      <label style={{ display: "grid", gap: 6, fontSize: 13.5 }}>
        Keahlian (pisahkan koma)
        <input
          value={skills}
          onChange={(e) => setSkills(e.target.value)}
          style={inputStyle}
          placeholder="Python, Machine Learning"
        />
      </label>
      <label style={{ display: "grid", gap: 6, fontSize: 13.5 }}>
        Minat kategori (beasiswa, magang, riset…)
        <input
          value={interests}
          onChange={(e) => setInterests(e.target.value)}
          style={inputStyle}
        />
      </label>

      <button className="primary-button" type="submit" disabled={busy}>
        {busy ? "Menyimpan…" : saved ? "Tersimpan ✓" : "Simpan profil"}
      </button>

      <div
        style={{
          paddingTop: 18,
          borderTop: "1px solid var(--line)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 14,
          flexWrap: "wrap",
        }}
      >
        <div>
          <strong style={{ fontSize: 14.5 }}>Notifikasi Telegram</strong>
          <p style={{ fontSize: 13, color: "var(--muted)" }}>
            Terima digest harian &amp; pengingat deadline via bot.
          </p>
        </div>
        {tgUrl ? (
          <a className="primary-button" href={tgUrl} target="_blank" rel="noreferrer">
            Hubungkan Telegram →
          </a>
        ) : (
          <button
            className="secondary-button"
            type="button"
            onClick={async () => {
              try {
                const r = await fetch("http://localhost:8000/telegram/link");
                const d = await r.json();
                setTgUrl(d.url);
              } catch {}
            }}
          >
            Buat tautan bot
          </button>
        )}
      </div>
    </form>
  );
}
