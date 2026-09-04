import { API_URL } from "../../lib/api";
import ProfileForm from "./form";

async function getProfile() {
  try {
    const res = await fetch(`${API_URL}/profile`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default async function ProfilePage() {
  const profile = await getProfile();

  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Profil akademik</h1>
      <p className="page-sub">
        Profil lengkap membuat eligibility dan rekomendasi jauh lebih akurat.
      </p>
      <ProfileForm initial={profile} />
    </main>
  );
}
