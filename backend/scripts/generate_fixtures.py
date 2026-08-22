"""Generate fixture corpus: 10 HTML, 10 PDF, 10 image files + expected outputs."""
import json
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"

HTML_FIXTURES = [
    {
        "filename": "beasiswa_lpdp_2026.html",
        "title": "Beasiswa LPDP 2026 Tahap 1",
        "content": """<html><head><title>Beasiswa LPDP 2026 Tahap 1 | LPDP</title></head><body>
<h1>Beasiswa LPDP 2026 Tahap 1</h1>
<p>Beasiswa penuh untuk studi S2 dan S3 dalam dan luar negeri.</p>
<p>Diselenggarakan oleh Kementerian Keuangan RI</p>
<p>Deadline: 31 Maret 2026</p>
<p>Persyaratan: IPK minimal 3.00</p>
<p>Lokasi: Seluruh Indonesia</p>
</body></html>""",
        "expected": {"title": "Beasiswa LPDP 2026 Tahap 1", "category": "beasiswa", "end_date": "2026-03-31", "organizer": "Kementerian Keuangan RI", "gpa_requirement": 3.0},
    },
    {
        "filename": "magang_kampus_merdeka.html",
        "title": "Magang Bersertifikat Kampus Merdeka Batch 8",
        "content": """<html><head><title>Magang Bersertifikat Kampus Merdeka Batch 8</title></head><body>
<h1>Magang Bersertifikat Kampus Merdeka Batch 8</h1>
<p>Program magang 6 bulan di perusahaan mitra dengan konversi 20 SKS.</p>
<p>Penyelenggara: Kemdikbudristek</p>
<p>Batas akhir pendaftaran: 28 Februari 2026</p>
<p>Lokasi: Seluruh Indonesia</p>
</body></html>""",
        "expected": {"title": "Magang Bersertifikat Kampus Merdeka Batch 8", "category": "magang", "end_date": "2026-02-28", "organizer": "Kemdikbudristek"},
    },
    {
        "filename": "lomba_data_science.html",
        "title": "Kompetisi Data Science Nasional 2026",
        "content": """<html><head><title>Kompetisi Data Science Nasional 2026</title></head><body>
<h1>Kompetisi Data Science Nasional 2026</h1>
<p>Kompetisi analisis data untuk mahasiswa S1 seluruh Indonesia.</p>
<p>Diselenggarakan oleh Universitas Indonesia</p>
<p>Deadline: 15 April 2026</p>
<p>Total hadiah: Rp 100.000.000</p>
<p>Bertempat di Jakarta</p>
</body></html>""",
        "expected": {"title": "Kompetisi Data Science Nasional 2026", "category": "lomba", "end_date": "2026-04-15", "organizer": "Universitas Indonesia", "prize": "Rp 100.000.000"},
    },
    {
        "filename": "fellowship_ai_brin.html",
        "title": "Fellowship Riset AI Indonesia",
        "content": """<html><head><title>Fellowship Riset AI Indonesia</title></head><body>
<h1>Fellowship Riset AI Indonesia</h1>
<p>Fellowship riset 3 bulan di bidang AI untuk mahasiswa S2.</p>
<p>Penyelenggara: BRIN</p>
<p>Batas waktu: 1 Mei 2026</p>
<p>Lokasi: Bandung</p>
</body></html>""",
        "expected": {"title": "Fellowship Riset AI Indonesia", "category": "fellowship", "end_date": "2026-05-01", "organizer": "BRIN"},
    },
    {
        "filename": "konferensi_teknologi.html",
        "title": "Konferensi Teknologi Mahasiswa Nasional",
        "content": """<html><head><title>Konferensi Teknologi Mahasiswa Nasional</title></head><body>
<h1>Konferensi Teknologi Mahasiswa Nasional</h1>
<p>Konferensi tahunan presentasi paper teknologi oleh mahasiswa.</p>
<p>Diselenggarakan oleh ITB</p>
<p>Deadline submission: 30 Juni 2026</p>
<p>Bertempat di Bandung</p>
</body></html>""",
        "expected": {"title": "Konferensi Teknologi Mahasiswa Nasional", "category": "konferensi", "end_date": "2026-06-30", "organizer": "ITB"},
    },
    {
        "filename": "volunteer_desa_digital.html",
        "title": "Volunteer Mengajar Desa Digital",
        "content": """<html><head><title>Volunteer Mengajar Desa Digital</title></head><body>
<h1>Volunteer Mengajar Desa Digital</h1>
<p>Program volunteer literasi digital di desa-desa selama 2 minggu.</p>
<p>Penyelenggara: Kominfo</p>
<p>Batas akhir: 15 Maret 2026</p>
<p>Lokasi: Jawa Tengah</p>
</body></html>""",
        "expected": {"title": "Volunteer Mengajar Desa Digital", "category": "volunteer", "end_date": "2026-03-15", "organizer": "Kominfo"},
    },
    {
        "filename": "pelatihan_cloud.html",
        "title": "Pelatihan Cloud Computing Gratis",
        "content": """<html><head><title>Pelatihan Cloud Computing Gratis</title></head><body>
<h1>Pelatihan Cloud Computing Gratis</h1>
<p>Pelatihan gratis Google Cloud Platform untuk mahasiswa.</p>
<p>Diselenggarakan oleh Google Developer Student Club</p>
<p>Deadline: 20 Februari 2026</p>
<p>Lokasi: Online</p>
</body></html>""",
        "expected": {"title": "Pelatihan Cloud Computing Gratis", "category": "pelatihan", "end_date": "2026-02-20", "organizer": "Google Developer Student Club"},
    },
    {
        "filename": "beasiswa_unggulan.html",
        "title": "Beasiswa Unggulan Kemendikbud 2026",
        "content": """<html><head><title>Beasiswa Unggulan Kemendikbud 2026</title></head><body>
<h1>Beasiswa Unggulan Kemendikbud 2026</h1>
<p>Beasiswa S1/S2/S3 untuk mahasiswa berprestasi.</p>
<p>Penyelenggara: Kemdikbudristek</p>
<p>Pendaftaran ditutup pada 31 Juli 2026</p>
<p>Persyaratan: IPK minimal 3.25</p>
<p>Lokasi: Seluruh Indonesia</p>
</body></html>""",
        "expected": {"title": "Beasiswa Unggulan Kemendikbud 2026", "category": "beasiswa", "end_date": "2026-07-31", "organizer": "Kemdikbudristek", "gpa_requirement": 3.25},
    },
    {
        "filename": "lomba_business_plan.html",
        "title": "Lomba Business Plan Nasional",
        "content": """<html><head><title>Lomba Business Plan Nasional</title></head><body>
<h1>Lomba Business Plan Nasional</h1>
<p>Kompetisi rencana bisnis untuk mahasiswa dengan mentoring.</p>
<p>Diselenggarakan oleh Universitas Gadjah Mada</p>
<p>Deadline: 30 April 2026</p>
<p>Berhadiah total Rp 50.000.000</p>
<p>Bertempat di Yogyakarta</p>
</body></html>""",
        "expected": {"title": "Lomba Business Plan Nasional", "category": "lomba", "end_date": "2026-04-30", "organizer": "Universitas Gadjah Mada"},
    },
    {
        "filename": "riset_brin.html",
        "title": "Program Riset Mahasiswa BRIN",
        "content": """<html><head><title>Program Riset Mahasiswa BRIN</title></head><body>
<h1>Program Riset Mahasiswa BRIN</h1>
<p>Pendanaan riset mahasiswa S1/S2 di laboratorium BRIN.</p>
<p>Penyelenggara: BRIN</p>
<p>Batas akhir: 31 Agustus 2026</p>
<p>Lokasi: Seluruh Indonesia</p>
</body></html>""",
        "expected": {"title": "Program Riset Mahasiswa BRIN", "category": "riset", "end_date": "2026-08-31", "organizer": "BRIN"},
    },
]

PDF_FIXTURES = [
    {"filename": "beasiswa_djarum.pdf", "title": "Beasiswa Djarum Plus 2026", "text": "Beasiswa Djarum Plus 2026\nBeasiswa untuk mahasiswa S1 berprestasi.\nPenyelenggara: Djarum Foundation\nDeadline: 20 Mei 2026\nPersyaratan: IPK minimal 3.20\nLokasi: Seluruh Indonesia"},
    {"filename": "lomba_hackathon.pdf", "title": "Hackathon Nasional 2026", "text": "Hackathon Nasional 2026\nKompetisi coding 48 jam untuk mahasiswa.\nDiselenggarakan oleh Dicoding\nBatas akhir: 10 Juni 2026\nTotal hadiah: Rp 75.000.000\nBertempat di Jakarta"},
    {"filename": "magang_bumn.pdf", "title": "Magang BUMN 2026", "text": "Magang BUMN 2026\nProgram magang di perusahaan BUMN selama 6 bulan.\nPenyelenggara: Kementerian BUMN\nDeadline: 15 Maret 2026\nLokasi: Seluruh Indonesia"},
    {"filename": "fellowship_kominfo.pdf", "title": "Fellowship Digital Talent Kominfo", "text": "Fellowship Digital Talent Kominfo\nProgram fellowship pelatihan digital untuk fresh graduate.\nDiselenggarakan oleh Kominfo\nBatas waktu: 25 April 2026\nLokasi: Online"},
    {"filename": "konferensi_ilmiah.pdf", "title": "Konferensi Ilmiah Mahasiswa Nasional", "text": "Konferensi Ilmiah Mahasiswa Nasional\nPresentasi hasil penelitian mahasiswa.\nPenyelenggara: Universitas Airlangga\nDeadline: 18 Juli 2026\nBertempat di Surabaya"},
    {"filename": "volunteer_lingkungan.pdf", "title": "Volunteer Lingkungan Hidup", "text": "Volunteer Lingkungan Hidup\nProgram volunteer penanaman mangrove.\nDiselenggarakan oleh WALHI\nBatas akhir: 5 Maret 2026\nLokasi: Kalimantan"},
    {"filename": "pelatihan_ai.pdf", "title": "Pelatihan AI dan Machine Learning", "text": "Pelatihan AI dan Machine Learning\nTraining intensif 3 bulan untuk mahasiswa.\nPenyelenggara: Coursera x Kampus Merdeka\nDeadline: 28 Februari 2026\nLokasi: Online"},
    {"filename": "beasiswa_tanoto.pdf", "title": "Beasiswa Tanoto Foundation 2026", "text": "Beasiswa Tanoto Foundation 2026\nBeasiswa penuh S1 untuk mahasiswa berprestasi.\nDiselenggarakan oleh Tanoto Foundation\nPendaftaran ditutup pada 30 Juni 2026\nPersyaratan: IPK minimal 3.25\nLokasi: Seluruh Indonesia"},
    {"filename": "lomba_esai.pdf", "title": "Lomba Esai Nasional 2026", "text": "Lomba Esai Nasional 2026\nKompetisi menulis esai untuk mahasiswa.\nPenyelenggara: Universitas Diponegoro\nDeadline: 22 Mei 2026\nBerhadiah total Rp 30.000.000\nBertempat di Semarang"},
    {"filename": "riset_kedokteran.pdf", "title": "Program Riset Kedokteran 2026", "text": "Program Riset Kedokteran 2026\nPendanaan riset untuk mahasiswa kedokteran.\nDiselenggarakan oleh IDI\nBatas akhir: 10 September 2026\nLokasi: Seluruh Indonesia"},
]

IMAGE_FIXTURES = [
    {"filename": "poster_beasiswa_chevening.png", "title": "Beasiswa Chevening 2026", "text": "Beasiswa Chevening 2026\nDeadline: 3 November 2026\nPenyelenggara: British Council\nLokasi: Inggris"},
    {"filename": "poster_lomba_foto.png", "title": "Lomba Fotografi Nasional", "text": "Lomba Fotografi Nasional\nBatas akhir: 12 April 2026\nHadiah: Rp 25.000.000\nPenyelenggara: Kompas"},
    {"filename": "poster_magang_startup.png", "title": "Magang Startup Batch 5", "text": "Magang Startup Batch 5\nDeadline: 8 Maret 2026\nPenyelenggara: GoTo Group\nLokasi: Jakarta"},
    {"filename": "poster_fellowship_jurnalis.png", "title": "Fellowship Jurnalis Muda", "text": "Fellowship Jurnalis Muda\nBatas waktu: 20 Mei 2026\nPenyelenggara: AJI Indonesia"},
    {"filename": "poster_seminar_ekonomi.png", "title": "Seminar Ekonomi Digital", "text": "Seminar Ekonomi Digital\nDeadline: 14 Juni 2026\nPenyelenggara: Bank Indonesia\nBertempat di Jakarta"},
    {"filename": "poster_volunteer_pendidikan.png", "title": "Volunteer Pendidikan Anak", "text": "Volunteer Pendidikan Anak\nBatas akhir: 1 Maret 2026\nPenyelenggara: Yayasan Pendidikan Indonesia"},
    {"filename": "poster_workshop_design.png", "title": "Workshop UI/UX Design", "text": "Workshop UI/UX Design\nDeadline: 25 Februari 2026\nPenyelenggara: Rakamin Academy\nLokasi: Online"},
    {"filename": "poster_beasiswa_fulbright.png", "title": "Beasiswa Fulbright 2026", "text": "Beasiswa Fulbright 2026\nDeadline: 15 Februari 2026\nPenyelenggara: AMINEF\nLokasi: Amerika Serikat"},
    {"filename": "poster_kompetisi_robotik.png", "title": "Kompetisi Robotik Nasional", "text": "Kompetisi Robotik Nasional\nBatas akhir: 30 Mei 2026\nHadiah: Rp 60.000.000\nPenyelenggara: ITS Surabaya"},
    {"filename": "poster_pelatihan_bisnis.png", "title": "Pelatihan Kewirausahaan Muda", "text": "Pelatihan Kewirausahaan Muda\nDeadline: 17 Juli 2026\nPenyelenggara: Kemenkop UKM\nLokasi: Seluruh Indonesia"},
]


def generate_html():
    out = FIXTURES / "html"
    out.mkdir(parents=True, exist_ok=True)
    for f in HTML_FIXTURES:
        (out / f["filename"]).write_text(f["content"], encoding="utf-8")
    print(f"Generated {len(HTML_FIXTURES)} HTML fixtures")


def generate_pdf():
    from pypdf import PdfWriter

    out = FIXTURES / "pdf"
    out.mkdir(parents=True, exist_ok=True)
    for f in PDF_FIXTURES:
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.add_metadata({"/Title": f["title"], "/Subject": f["text"]})
        with open(out / f["filename"], "wb") as fp:
            writer.write(fp)
    print(f"Generated {len(PDF_FIXTURES)} PDF fixtures (metadata-based)")


def generate_images():
    from PIL import Image, ImageDraw, ImageFont

    out = FIXTURES / "image"
    out.mkdir(parents=True, exist_ok=True)
    for f in IMAGE_FIXTURES:
        img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except OSError:
            font = ImageFont.load_default()
        y = 50
        for line in f["text"].split("\n"):
            draw.text((50, y), line, fill=(0, 0, 0), font=font)
            y += 60
        img.save(out / f["filename"])
    print(f"Generated {len(IMAGE_FIXTURES)} image fixtures")


def generate_expected():
    out = FIXTURES / "expected"
    out.mkdir(parents=True, exist_ok=True)
    expected = {}
    for f in HTML_FIXTURES:
        expected[f["filename"]] = {**f["expected"], "doc_type": "HTML"}
    for f in PDF_FIXTURES:
        expected[f["filename"]] = {"title": f["title"], "doc_type": "PDF"}
    for f in IMAGE_FIXTURES:
        expected[f["filename"]] = {"title": f["title"], "doc_type": "IMAGE"}
    (out / "expected.json").write_text(json.dumps(expected, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated expected.json with {len(expected)} entries")


if __name__ == "__main__":
    generate_html()
    generate_pdf()
    generate_images()
    generate_expected()
    print("Done! 30 fixtures generated.")
