type FeedItem = {
  id?: string;
  opportunity_id?: string;
  title: string;
  slug: string;
  category: string;
  organizer?: string;
  location?: string;
  end_date?: string;
  prize?: string;
  score?: number;
};

async function getFeed(): Promise<FeedItem[]> {
  const API = "http://localhost:8000";
  try {
    const res = await fetch(`${API}/recommendations?limit=8`, { cache: "no-store" });
    if (res.ok) {
      const recs = await res.json();
      if (recs.length > 0) return recs;
    }
    const res2 = await fetch(`${API}/opportunities?limit=8`, { cache: "no-store" });
    if (!res2.ok) return [];
    const opps = await res2.json();
    return (opps as FeedItem[]).map((o) => ({
      ...o,
      opportunity_id: o.opportunity_id ?? o.id,
    }));
  } catch {
    return [];
  }
}

async function getProfile() {
  try {
    const res = await fetch("http://localhost:8000/profile", { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function daysLeft(endDate?: string) {
  if (!endDate) return "—";
  const diff = Math.ceil((new Date(endDate).getTime() - Date.now()) / 86_400_000);
  if (diff < 0) return "lewat";
  if (diff === 0) return "hari ini!";
  return `${diff}h`;
}

const categoryLabels: Record<string, string> = {
  beasiswa: "Beasiswa",
  lomba: "Lomba",
  magang: "Magang",
  fellowship: "Fellowship",
  konferensi: "Konferensi",
  volunteer: "Volunteer",
  pelatihan: "Pelatihan",
  riset: "Riset",
  kompetisi: "Kompetisi",
};

export default async function HomePage() {
  const [feed, profile] = await Promise.all([getFeed(), getProfile()]);
  const total = feed.length;
  const soonest = feed
    .filter((f) => f.end_date)
    .sort((a, b) => (a.end_date! < b.end_date! ? -1 : 1))[0];

  return (
    <main className="one-shell">
      {/* ===== HEADER ===== */}
      <header className="one-header">
        <div className="brand-lockup">
          <span className="brand-mark">P</span>
          <span>Peluang<span style={{ color: "var(--accent)" }}>.ai</span></span>
        </div>
        <nav className="one-nav">
          <a href="#feed">Peluang</a>
          <a href="#saved">Tersimpan</a>
          <a href="#dilamar">Lamaran</a>
          <a href="#profil">Profil</a>
          <a href="#pengaturan">Pipeline</a>
          <a href="/dashboard" className="nav-cmd">▪ cmd</a>
        </nav>
      </header>

      {/* ===== HERO COMPACT ===== */}
      <section className="one-hero">
        <div>
          <h1>
            {profile?.major
              ? `Halo, ${profile.major} 👋`
              : "Temukan peluangmu."}
          </h1>
          <p>
            {total > 0
              ? `${total} peluang cocok untukmu${soonest ? ` — terdekat tinggal ${daysLeft(soonest.end_date)}` : ""}.`
              : "Pipeline sedang mengumpulkan peluang. Kembali sebentar lagi."}
          </p>
          <div className="one-hero-cta">
            <a className="primary-button" href="#feed">Lihat peluang</a>
            <a className="secondary-button" href="#profil">Lengkapi profil</a>
          </div>
        </div>
        <div className="one-hero-stats">
          <div>
            <strong>{total}</strong>
            <span>peluang aktif</span>
          </div>
          <div>
            <strong>{new Set(feed.map((f) => f.category)).size}</strong>
            <span>kategori</span>
          </div>
          <div>
            <strong>
              {soonest ? daysLeft(soonest.end_date) : "—"}
            </strong>
            <span>deadline terdekat</span>
          </div>
        </div>
      </section>

      {/* ===== FEED ===== */}
      <section id="feed" className="one-section">
        <div className="one-section-head">
          <h2>Peluang untukmu</h2>
          <a href="/explore" className="one-more">Jelajahi semua →</a>
        </div>

        {feed.length === 0 ? (
          <div className="empty-state">
            <h3>Belum ada peluang.</h3>
            <p>Jalankan pipeline di bagian bawah halaman ini, atau tunggu crawl harian 07:00.</p>
          </div>
        ) : (
          <div className="one-grid">
            {feed.map((item, i) => (
              <article key={item.opportunity_id ?? item.id} className="feed-card">
                <div className="feed-card-top">
                  <span className="category-chip">
                    {categoryLabels[item.category] ?? item.category}
                  </span>
                  <span className="deadline-chip">
                    {item.end_date ? `${daysLeft(item.end_date)} · ${item.end_date}` : "deadline —"}
                  </span>
                </div>
                <h3>
                  <a href={`/opportunity/${item.slug}`}>{item.title}</a>
                </h3>
                <p>{item.organizer ?? "Penyelenggara belum tercatat"}</p>
                <div className="feed-card-bottom">
                  <span>{item.location ?? "Fleksibel"}</span>
                  <a href={`/opportunity/${item.slug}`}>Detail →</a>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* ===== SAVED + APPLIED (tabs kecil via 2 kolom) ===== */}
      <div className="one-cols">
        <SavedColumn />
        <AppliedColumn />
      </div>

      {/* ===== PROFIL + PIPELINE ===== */}
      <div className="one-cols one-cols-2">
        <ProfileCard profile={profile} />
        <PipelineCard />
      </div>

      <footer className="one-footer">
        <span>Peluang.ai — self-hosted · data lokal</span>
        <a href="/dashboard">Command Center</a>
      </footer>
    </main>
  );
}

/* --- server sub-components --- */

async function SavedColumn() {
  let items: FeedItem[] = [];
  try {
    const r = await fetch("http://localhost:8000/profile/saved", { cache: "no-store" });
    if (r.ok) items = await r.json();
  } catch {}
  return (
    <section id="saved" className="one-section">
      <div className="one-section-head">
        <h2>Tersimpan</h2>
        <span className="one-count">{items.length}</span>
      </div>
      <ItemRows items={items} empty="Belum ada. Tekan Simpan di halaman detail peluang." />
    </section>
  );
}

async function AppliedColumn() {
  let items: FeedItem[] = [];
  try {
    const r = await fetch("http://localhost:8000/profile/applied", { cache: "no-store" });
    if (r.ok) items = await r.json();
  } catch {}
  return (
    <section id="dilamar" className="one-section">
      <div className="one-section-head">
        <h2>Lamaran</h2>
        <span className="one-count">{items.length}</span>
      </div>
      <ItemRows items={items} empty="Belum ada. Tekan Tandai Dilamar di detail peluang." />
    </section>
  );
}

function ItemRows({ items, empty }: { items: FeedItem[]; empty: string }) {
  if (items.length === 0) return <p className="one-empty">{empty}</p>;
  return (
    <div className="one-rows">
      {items.map((it) => (
        <a key={it.opportunity_id ?? it.id} href={`/opportunity/${it.slug}`} className="one-row">
          <span className="category-chip">{it.category}</span>
          <span className="one-row-title">{it.title}</span>
          <span className="one-row-date">{it.end_date ?? ""}</span>
        </a>
      ))}
    </div>
  );
}

function ProfileCard({ profile }: { profile: Record<string, unknown> | null }) {
  const fields: Array<[string, unknown]> = [
    ["Jurusan", profile?.major],
    ["Universitas", profile?.university],
    ["IPK", profile?.cgpa],
    ["Keahlian", Array.isArray(profile?.skills) ? (profile?.skills as string[]).join(", ") : null],
    ["Domisili", profile?.location],
  ];
  return (
    <section id="profil" className="one-section">
      <div className="one-section-head">
        <h2>Profil</h2>
        <a href="/profile" className="one-more">Edit lengkap →</a>
      </div>
      <div className="one-rows">
        {fields.map(([k, v]) => (
          <div key={k} className="one-row">
            <span className="one-row-k">{k}</span>
            <span className="one-row-v">{v ? String(v) : "—"}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function PipelineCard() {
  return (
    <section id="pengaturan" className="one-section">
      <div className="one-section-head">
        <h2>Pipeline</h2>
        <a href="/settings" className="one-more">Pengaturan →</a>
      </div>
      <div className="one-pipe">
        <div>
          <strong>Crawl + LLM lokal</strong>
          <p>Ollama llama3.2 — gratis, tanpa limit</p>
        </div>
        <div className="one-pipe-actions">
          <a className="primary-button" href="/settings">Kontrol</a>
          <a className="secondary-button" href="/dashboard">Stream</a>
        </div>
      </div>
    </section>
  );
}
