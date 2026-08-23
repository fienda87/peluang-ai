const profileFields: Array<[string, string]> = [
  ["Jenjang pendidikan", "Belum diisi"],
  ["Jurusan", "Belum diisi"],
  ["Universitas", "Belum diisi"],
  ["IPK", "Belum diisi"],
  ["Keahlian", "Belum diisi"],
  ["Minat", "Belum diisi"],
];

export default function ProfilePage() {
  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Profil akademik</h1>
      <p className="page-sub">
        Profil yang lengkap membuat eligibility check dan ranking rekomendasi jauh lebih akurat.
      </p>

      <div className="simple-card">
        <dl className="detail-facts">
          {profileFields.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        <div className="action-row">
          <button className="primary-button" type="button">Lengkapi profil</button>
        </div>
      </div>
    </main>
  );
}
