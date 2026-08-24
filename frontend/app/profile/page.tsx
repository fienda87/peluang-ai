"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, getToken } from "../../lib/auth";

type Profile = {
  education_level?: string;
  major?: string;
  university?: string;
  graduation_year?: number;
  cgpa?: number;
  skills?: string[];
  interests?: string[];
  goals?: string[];
  location?: string;
};

const FIELDS: Array<{ key: keyof Profile; label: string; type?: string }> = [
  { key: "education_level", label: "Jenjang pendidikan" },
  { key: "major", label: "Jurusan" },
  { key: "university", label: "Universitas" },
  { key: "graduation_year", label: "Tahun lulus", type: "number" },
  { key: "cgpa", label: "IPK", type: "number" },
  { key: "location", label: "Domisili" },
];

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile>({});
  const [skills, setSkills] = useState("");
  const [interests, setInterests] = useState("");
  const [authed, setAuthed] = useState(true);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      setAuthed(false);
      return;
    }
    api<Profile>("/profile")
      .then((p) => {
        setProfile(p || {});
        setSkills((p.skills || []).join(", "));
        setInterests((p.interests || []).join(", "));
      })
      .catch(() => setAuthed(false));
  }, []);

  async function save() {
    setBusy(true);
    try {
      await api("/profile", {
        method: "PUT",
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
    } catch {
      alert("Gagal menyimpan.");
    } finally {
      setBusy(false);
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
            </Link>{" "}
            untuk mengisi profil.
          </p>
        </div>
      </main>
    );
  }

  const inputStyle = {
    height: 44,
    padding: "0 12px",
    border: "1px solid var(--line)",
    borderRadius: 10,
    fontSize: 14,
    width: "100%",
  };

  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Profil akademik</h1>
      <p className="page-sub">
        Profil lengkap membuat eligibility dan rekomendasi jauh lebih akurat.
      </p>

      <form className="simple-card" onSubmit={(e) => { e.preventDefault(); save(); }} style={{ display: "grid", gap: 16 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
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
          <input value={skills} onChange={(e) => setSkills(e.target.value)} style={inputStyle} placeholder="Python, Machine Learning" />
        </label>
        <label style={{ display: "grid", gap: 6, fontSize: 13.5 }}>
          Minat kategori (beasiswa, magang, riset…)
          <input value={interests} onChange={(e) => setInterests(e.target.value)} style={inputStyle} />
        </label>

        <button className="primary-button" type="submit" disabled={busy}>
          {busy ? "Menyimpan…" : saved ? "Tersimpan ✓" : "Simpan profil"}
        </button>
      </form>
    </main>
  );
}
