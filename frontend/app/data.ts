export type Opportunity = {
  id?: string;
  opportunity_id?: string;
  title: string;
  slug: string;
  category: string;
  organizer?: string | null;
  location?: string | null;
  end_date?: string | null;
  prize?: string | null;
  score?: number;
  eligibility?: "ELIGIBLE" | "INELIGIBLE" | "UNKNOWN";
  reasoning?: { reason?: string };
};

export const demoOpportunities: Opportunity[] = [
  {
    id: "demo-1",
    opportunity_id: "demo-1",
    title: "Beasiswa LPDP 2026 Tahap 1",
    slug: "beasiswa-lpdp-2026-tahap-1",
    category: "beasiswa",
    organizer: "Kementerian Keuangan RI",
    location: "Seluruh Indonesia",
    end_date: "2026-03-31",
    score: 0.94,
    eligibility: "ELIGIBLE",
    reasoning: { reason: "Cocok dengan minat beasiswa dan profil akademikmu." },
  },
  {
    id: "demo-2",
    opportunity_id: "demo-2",
    title: "Magang Bersertifikat Kampus Merdeka Batch 8",
    slug: "magang-kampus-merdeka-batch-8",
    category: "magang",
    organizer: "Kemdikbudristek",
    location: "Seluruh Indonesia",
    end_date: "2026-02-28",
    score: 0.87,
    eligibility: "UNKNOWN",
    reasoning: { reason: "Relevan untuk pengalaman kerja awal, tapi syarat jurusan perlu dicek." },
  },
  {
    id: "demo-3",
    opportunity_id: "demo-3",
    title: "Kompetisi Data Science Nasional 2026",
    slug: "kompetisi-data-science-2026",
    category: "lomba",
    organizer: "Universitas Indonesia",
    location: "Jakarta",
    end_date: "2026-04-15",
    prize: "Rp 100.000.000",
    score: 0.81,
    eligibility: "ELIGIBLE",
    reasoning: { reason: "Skill Python dan data analysis cocok dengan tema kompetisi." },
  },
  {
    id: "demo-4",
    opportunity_id: "demo-4",
    title: "Program Riset Mahasiswa BRIN",
    slug: "program-riset-mahasiswa-brin-2026",
    category: "riset",
    organizer: "BRIN",
    location: "Seluruh Indonesia",
    end_date: "2026-08-31",
    score: 0.76,
    eligibility: "UNKNOWN",
    reasoning: { reason: "Sesuai tujuan riset, tetapi topik final perlu dibandingkan dengan minatmu." },
  },
];

export function bySlug(slug: string) {
  return demoOpportunities.find((item) => item.slug === slug) ?? null;
}
