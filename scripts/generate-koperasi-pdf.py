#!/usr/bin/env python3
"""
Generate Organizational Structure & Workflow PDF for Koperasi TKW Taiwan
Two versions: Bahasa Indonesia and Traditional Mandarin
"""

from fpdf import FPDF
import os

# ============================================================
# CONFIG
# ============================================================
OUTPUT_DIR = "/home/ubuntu/meridian/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Font paths
FONT_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_MEDIUM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"

# Colors
DARK_BLUE = (25, 55, 109)
MEDIUM_BLUE = (41, 85, 150)
LIGHT_BLUE = (220, 235, 255)
GOLD = (212, 175, 55)
DARK_GRAY = (60, 60, 60)
MED_GRAY = (140, 140, 140)
LIGHT_GRAY = (245, 245, 245)
WHITE = (255, 255, 255)
GREEN = (40, 140, 80)
RED = (180, 50, 50)
ORANGE = (220, 140, 30)

# ============================================================
# CUSTOM PDF CLASS
# ============================================================
class KoperasiPDF(FPDF):
    def __init__(self, lang="id", title="", subtitle=""):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.lang = lang
        self.doc_title = title
        self.doc_subtitle = subtitle
        self.add_font("Noto", "", FONT_REGULAR, uni=True)
        self.add_font("Noto", "B", FONT_BOLD, uni=True)
        self.add_font("Noto", "B", FONT_MEDIUM, uni=True)  # Also register medium as bold for "B" style
        # Note: fpdf2 only supports styles "", "B", "I", "BI", "U", "S", "BU"
        # We'll use "B" where we wanted medium
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Noto", "", 7)
            self.set_text_color(*MED_GRAY)
            self.cell(0, 5, self.doc_title, align="L")
            self.cell(0, 5, f"Hal. {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(*LIGHT_BLUE)
            self.line(10, 12, 200, 12)
            self.ln(5)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Noto", "", 6)
            self.set_text_color(*MED_GRAY)
            self.cell(0, 10, f"Koperasi TKW Taiwan — {self.doc_title}", align="C")

    def section_title(self, title, num=None):
        self.ln(4)
        prefix = f"{num}. " if num else ""
        self.set_font("Noto", "B", 14)
        self.set_text_color(*DARK_BLUE)
        # Gold left bar
        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(*GOLD)
        self.rect(x, y, 3, 8, style="F")
        self.set_x(x + 6)
        self.cell(0, 8, f"{prefix}{title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def sub_title(self, title):
        self.ln(2)
        self.set_font("Noto", "B", 11)
        self.set_text_color(*MEDIUM_BLUE)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text, size=9):
        self.set_font("Noto", "", size)
        self.set_text_color(*DARK_GRAY)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text, size=9):
        self.set_font("Noto", "", size)
        self.set_text_color(*DARK_GRAY)
        self.set_x(self.l_margin)
        indent = 5
        self.cell(indent, 5.5, ">")
        w = self.w - self.l_margin - self.r_margin - indent
        self.multi_cell(w, 5.5, text)

    def colored_box(self, x, y, w, h, color, text="", text_color=None, font_size=8, bold=False, align="C"):
        """Draw a colored rectangle with centered text"""
        self.set_fill_color(*color)
        r = self.rect(x, y, w, h, style="F")
        if text:
            if bold:
                self.set_font("Noto", "B", font_size)
            else:
                self.set_font("Noto", "", font_size)
            self.set_text_color(*(text_color or WHITE))
            # Calculate text position for centering
            tw = self.get_string_width(text)
            tx = x + (w - tw) / 2
            ty = y + (h - 5) / 2
            self.set_xy(max(tx, x + 1), ty)
            self.cell(min(tw, w - 2), 5, text, align=align)

    def draw_person(self, x, y, size=4, color=None):
        """Draw a simple person icon using circles and lines"""
        c = color or DARK_BLUE
        self.set_draw_color(*c)
        self.set_fill_color(*c)
        # Head (circle)
        head_r = size * 0.35
        self.circle(x, y - head_r, head_r)
        # Body (line down)
        body_len = size * 0.8
        self.line(x, y, x, y + body_len)
        # Arms
        arm_w = size * 0.5
        self.line(x - arm_w, y + body_len * 0.3, x + arm_w, y + body_len * 0.3)
        # Legs
        leg_w = size * 0.3
        leg_y = y + body_len
        self.line(x, leg_y, x - leg_w, leg_y + size * 0.4)
        self.line(x, leg_y, x + leg_w, leg_y + size * 0.4)

    def draw_org_box(self, x, y, w, h, title, subtitle="", color=None, people_count=0):
        """Draw an organizational unit box with optional people icons"""
        c = color or MEDIUM_BLUE
        # Outer rounded box - using normal rect since fpdf2 doesn't have easy rounded rect
        self.set_fill_color(*c)
        self.set_draw_color(*tuple(min(v + 30, 255) for v in c))
        self.set_line_width(0.5)
        self.rect(x, y, w, h, style="DF")

        # Title
        self.set_font("Noto", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(x + 2, y + 2)
        self.cell(w - 4, 5, title, align="C")

        # Subtitle
        if subtitle:
            self.set_font("Noto", "", 7)
            self.set_text_color(*WHITE)
            self.set_xy(x + 2, y + 7)
            self.cell(w - 4, 4, subtitle, align="C")

        # People icons
        if people_count > 0:
            py = y + h - 10
            spacing = w / (people_count + 1)
            for i in range(people_count):
                px = x + spacing * (i + 1)
                self.set_draw_color(*WHITE)
                self.set_fill_color(*WHITE)
                head_r = 2
                self.circle(px, py, head_r)
                self.line(px, py, px, py + 4)
                self.line(px - 2, py + 1.5, px + 2, py + 1.5)
                self.line(px, py + 4, px - 1.5, py + 6)
                self.line(px, py + 4, px + 1.5, py + 6)

    def draw_org_chart(self):
        """Draw the full organization structure"""
        cx = 105  # center x
        self.ln(5)

        # ---- TOP: Manager ----
        box_w = 55
        box_h = 18
        mx = cx - box_w / 2
        my = self.get_y()
        self.draw_org_box(mx, my, box_w, box_h, "MANAGER / KEPALA KOPERASI", "Manager / 經理", DARK_BLUE, 1)
        mgr_bottom = my + box_h

        # ---- Vertical line down from Manager ----
        line_x = cx
        line_y1 = mgr_bottom
        line_y2 = line_y1 + 12
        self.set_draw_color(*DARK_BLUE)
        self.set_line_width(1.5)
        self.line(line_x, line_y1, line_x, line_y2)

        # ---- Horizontal line ----
        h_line_y = line_y2
        h_left = 20
        h_right = 190
        self.line(h_left, h_line_y, h_right, h_line_y)

        # ---- Vertical lines down to each division ----
        div_x_positions = [37, 75, 105, 135, 173]
        for dx in div_x_positions:
            self.set_draw_color(*DARK_BLUE)
            self.set_line_width(1.5)
            self.line(dx, h_line_y, dx, h_line_y + 10)

        # ---- Divisions ----
        div_data = [
            ("DIVISI MARKETING", "行銷部", "Mencari &\nmensosialisasikan", GOLD, DARK_GRAY, 3),
            ("DIVISI CHECKING &\nADMINISTRASI", "審核行政部", "Verifikasi &\nvalidasi dokumen", MEDIUM_BLUE, WHITE, 3),
            ("DIVISI KEUANGAN &\nAKUNTING", "財務會計部", "Pencairan &\npembukuan", GREEN, WHITE, 3),
            ("DIVISI PENAGIHAN", "催收部", "Penagihan &\nfollow up", RED, WHITE, 3),
            ("SEKRETARIS &\nUMUM", "秘書總務", "Administrasi\n& umum", ORANGE, WHITE, 2),
        ]

        div_w = 32
        div_h = 40
        div_start_y = h_line_y + 10

        for i, (title, cn, desc, bg, tc, ppl) in enumerate(div_data):
            dx = div_x_positions[i] - div_w / 2
            self.draw_org_box(dx, div_start_y, div_w, div_h, title, cn, bg, ppl)
            # Small desc below
            self.set_font("Noto", "", 6)
            self.set_text_color(*DARK_GRAY)
            self.set_xy(dx, div_start_y + div_h + 2)
            self.cell(div_w, 4, desc, align="C")

        return div_start_y + div_h + 12

    def kpi_table(self, data, col_widths=None):
        """Draw a KPI table. data = list of rows, first row is header.
        If col_widths is None, auto-calculates based on available width."""
        page_w = self.w - self.l_margin - self.r_margin  # usually 180mm
        num_cols = len(data[0])

        if col_widths is None:
            # Auto-distribute evenly
            col_widths = [page_w / num_cols] * num_cols
        elif len(col_widths) != num_cols:
            # Mismatch: auto-fix
            col_widths = [page_w / num_cols] * num_cols

        # Header
        self.set_font("Noto", "B", 8)
        self.set_fill_color(*DARK_BLUE)
        self.set_text_color(*WHITE)
        for i, h in enumerate(data[0]):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Noto", "", 7.5)
        for row_idx, row in enumerate(data[1:]):
            if row_idx % 2 == 0:
                self.set_fill_color(*LIGHT_GRAY)
            else:
                self.set_fill_color(*WHITE)
            self.set_text_color(*DARK_GRAY)
            row_h = 6
            x_start = self.get_x()
            y_start = self.get_y()

            # Calculate max height needed
            max_h = row_h
            for i, cell_text in enumerate(row):
                lines = self.multi_cell(col_widths[i], row_h, cell_text, dry_run=True, output="LINES")
                cell_h = len(lines) * row_h
                max_h = max(max_h, cell_h)

            # Draw cells
            for i, cell_text in enumerate(row):
                x_cell = self.get_x()
                y_cell = self.get_y()
                self.set_xy(x_cell, y_cell)
                # Draw background
                self.rect(x_cell, y_cell, col_widths[i], max_h, style="F")
                # Draw border
                self.rect(x_cell, y_cell, col_widths[i], max_h, style="D")
                # Text
                self.set_xy(x_cell + 1, y_cell + 0.5)
                self.multi_cell(col_widths[i] - 2, row_h, cell_text)
                self.set_xy(x_cell + col_widths[i], y_cell)

            self.set_xy(x_start, y_start + max_h)

        self.ln(3)


# ============================================================
# INDONESIA VERSION CONTENT
# ============================================================
def build_indonesia():
    pdf = KoperasiPDF(
        lang="id",
        title="BUKU PEDOMAN ORGANISASI & ALUR KERJA",
        subtitle="Koperasi Simpan Pinjam TKW Taiwan"
    )
    pdf.set_margins(15, 10, 15)

    # ---- COVER PAGE ----
    pdf.add_page()
    pdf.ln(30)

    # Decorative top bar
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(15, pdf.get_y(), 180, 3, style="F")
    pdf.ln(8)

    # Title
    pdf.set_font("Noto", "B", 24)
    pdf.set_text_color(*DARK_BLUE)
    pdf.multi_cell(0, 12, "BUKU PEDOMAN\nORGANISASI & ALUR KERJA", align="C")
    pdf.ln(5)

    # Gold separator
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.8)
    y = pdf.get_y()
    pdf.line(70, y, 140, y)
    pdf.ln(8)

    # Subtitle
    pdf.set_font("Noto", "B", 14)
    pdf.set_text_color(*MEDIUM_BLUE)
    pdf.cell(0, 8, "Koperasi Simpan Pinjam TKW Taiwan", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # People icons row
    people_y = pdf.get_y()
    for i in range(7):
        px = 45 + i * 18
        pdf.set_draw_color(*DARK_BLUE)
        pdf.set_fill_color(*DARK_BLUE)
        pdf.circle(px, people_y, 4)
        pdf.line(px, people_y, px, people_y + 8)
        pdf.line(px - 4, people_y + 3, px + 4, people_y + 3)
        pdf.line(px, people_y + 8, px - 3, people_y + 13)
        pdf.line(px, people_y + 8, px + 3, people_y + 13)
    pdf.ln(20)

    # Info box
    pdf.set_fill_color(*LIGHT_BLUE)
    pdf.set_draw_color(*MEDIUM_BLUE)
    pdf.set_line_width(0.5)
    box_y = pdf.get_y()
    pdf.rect(30, box_y, 150, 30, style="DF")
    pdf.set_font("Noto", "", 9)
    pdf.set_text_color(*DARK_GRAY)
    pdf.set_xy(35, box_y + 4)
    pdf.cell(140, 5, "Untuk TKW Indonesia di Taiwan", align="C")
    pdf.set_xy(35, box_y + 11)
    pdf.cell(140, 5, "Pedoman Kerja Divisi | KPI Target | Alur Pengajuan Pinjaman", align="C")
    pdf.set_xy(35, box_y + 18)
    pdf.cell(140, 5, "Edisi: Juni 2026", align="C")

    pdf.ln(45)

    # Bottom bar
    pdf.set_fill_color(*GOLD)
    pdf.rect(15, pdf.get_y(), 180, 2, style="F")

    # ---- PAGE 2: DAFTAR ISI ----
    pdf.add_page()
    pdf.section_title("DAFTAR ISI")
    toc = [
        ("1", "Struktur Organisasi & Pembagian Tugas"),
        ("2", "Tugas Pokok Masing-masing Divisi"),
        ("3", "KPI (Key Performance Indicator) Target"),
        ("4", "Alur Kerja Pemberian Pinjaman (5 Tahap)"),
        ("5", "Alur Penagihan & Follow Up"),
        ("6", "Jadwal Rapat & Pelaporan Rutin"),
        ("7", "Pengendalian Internal & Cek SOP"),
        ("8", "Lampiran: Istilah Mandarin-Inggris"),
    ]
    for num, title in toc:
        pdf.set_font("Noto", "B", 10)
        pdf.set_text_color(*MEDIUM_BLUE)
        pdf.cell(10, 7, num)
        pdf.set_font("Noto", "", 10)
        pdf.set_text_color(*DARK_GRAY)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*LIGHT_BLUE)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

    # ---- PAGE 3: STRUKTUR ORGANISASI ----
    pdf.add_page()
    pdf.section_title("STRUKTUR ORGANISASI", 1)
    pdf.body_text(
        "Berikut adalah struktur organisasi Koperasi Simpan Pinjam TKW Taiwan. "
        "Setiap divisi bekerja sesuai tugas pokok masing-masing dan saling mendukung. "
        "Manager bertanggung jawab penuh terhadap jalannya operasional koperasi."
    )

    org_bottom = pdf.draw_org_chart()

    pdf.set_y(max(org_bottom, pdf.get_y() + 5))
    pdf.sub_title("Pembagian Tanggung Jawab")
    pdf.body_text(
        "MANAGER: Memimpin seluruh kegiatan koperasi, mengambil keputusan strategis, "
        "mengesahkan pencairan pinjaman di atas limit tertentu, dan bertanggung jawab "
        "kepada Rapat Anggota.\n\n"
        "SEKRETARIS & UMUM: Mendukung administrasi rapat, pengarsipan dokumen penting, "
        "dan pengelolaan logistik kantor.\n\n"
        "Setiap divisi bekerja secara terpisah tapi saling terhubung — hasil kerja satu "
        "divisi menjadi input bagi divisi berikutnya. Prinsip SEGREGASI TUGAS (pemisahan "
        "tugas) diterapkan untuk mencegah kesalahan dan penyalahgunaan wewenang."
    )

    # ---- PAGE 4-5: TUGAS POKOK ----
    pdf.add_page()
    pdf.section_title("TUGAS POKOK MASING-MASING DIVISI", 2)

    # Marketing
    pdf.sub_title("A. DIVISI MARKETING (行銷部)")
    pdf.body_text("Bertugas mencari dan mensosialisasikan koperasi kepada TKW Indonesia di Taiwan.")
    for b in [
        "Menyebarkan informasi koperasi melalui media sosial, grup, dan referral.",
        "Menjelaskan syarat & ketentuan pinjaman kepada calon anggota.",
        "Mengumpulkan data awal calon anggota (formulir pendaftaran, KTP, kontrak kerja).",
        "Menjaga hubungan baik dengan anggota aktif (member care).",
        "Melaporkan calon anggota ke Divisi Checking untuk verifikasi lanjutan.",
    ]:
        pdf.bullet(b)

    # Checking
    pdf.sub_title("B. DIVISI CHECKING & ADMINISTRASI (審核行政部)")
    pdf.body_text("Bertugas memverifikasi kelengkapan dan keabsahan dokumen calon anggota.")
    for b in [
        "Memeriksa keaslian KTP, Kartu Keluarga, kontrak kerja Taiwan, dan paspor.",
        "Verifikasi data via WhatsApp/call dengan TKW dan pihak Taiwan (majikan/agen).",
        "Validasi slip gaji/rekening bank Taiwan selama 3 bulan terakhir.",
        "Input data anggota ke sistem (nama, alamat, nomor rekening Taiwan, dll).",
        "Membuat berkas pengajuan pinjaman untuk diteruskan ke Divisi Keuangan.",
    ]:
        pdf.bullet(b)

    # Finance
    pdf.sub_title("C. DIVISI KEUANGAN & AKUNTING (財務會計部)")
    pdf.body_text("Bertugas mencairkan pinjaman dan mencatat semua transaksi keuangan.")
    for b in [
        "Menyiapkan dana pencairan pinjaman sesuai limit yang disetujui Manager.",
        "Transfer dana ke rekening Taiwan TKW atau rekening Indonesia (sesuai perjanjian).",
        "Mencatat semua transaksi: penerimaan simpanan, pencairan pinjaman, angsuran, biaya.",
        "Menyusun laporan keuangan bulanan (Neraca, Laba Rugi, Arus Kas).",
        "Rekonsiliasi bank setiap akhir bulan.",
        "Menyetorkan PPh 21 dan pajak lainnya tepat waktu.",
    ]:
        pdf.bullet(b)

    # Collection
    pdf.sub_title("D. DIVISI PENAGIHAN (催收部)")
    pdf.body_text("Bertugas melakukan penagihan angsuran dan follow up pembayaran.")
    for b in [
        "Mengingatkan anggota via WA/call 3-5 hari sebelum jatuh tempo angsuran.",
        "Memantau pembayaran angsuran harian/mingguan/bulanan.",
        "Follow up anggota yang terlambat bayar (tahap: pengingat -> teguran -> kunjungan).",
        "Mencatat hasil penagihan di sistem (tanggal hubungi, respon, janji bayar).",
        "Melaporkan anggota bermasalah ke Manager untuk tindakan lebih lanjut.",
    ]:
        pdf.bullet(b)

    # ---- PAGE 6-7: KPI TARGET ----
    pdf.add_page()
    pdf.section_title("KPI (KEY PERFORMANCE INDICATOR) TARGET", 3)
    pdf.body_text(
        "Setiap divisi memiliki target KPI yang harus dicapai setiap bulan. "
        "Evaluasi KPI dilakukan setiap awal bulan pada rapat koordinasi. "
        "Target KPI ini bisa disesuaikan dengan kondisi koperasi."
    )

    # Marketing KPI
    pdf.sub_title("A. KPI DIVISI MARKETING")
    pdf.kpi_table([
        ["Indikator", "Target", "Cara Ukur"],
        ["Jumlah anggota baru", ">= 15 orang/bulan", "Hitung anggota yang masuk verifikasi"],
        ["Tingkat konversi", ">= 60%", "Anggota cair / calon anggota x 100%"],
        ["Member aktif dihubungi", ">= 80%", "Anggota aktif yang dihubungi / total anggota"],
        ["Keluhan anggota", "< 5 keluhan/bulan", "Catatan keluhan yang diterima"],
    ])

    # Checking KPI
    pdf.sub_title("B. KPI DIVISI CHECKING & ADMINISTRASI")
    pdf.kpi_table([
        ["Indikator", "Target", "Cara Ukur"],
        ["Waktu verifikasi", "<= 3 hari kerja", "Tgl terima berkas -> tgl selesai verifikasi"],
        ["Akurasi verifikasi", ">= 98%", "Berkas benar / total berkas x 100%"],
        ["Dokumen lengkap", ">= 90%", "Berkas lengkap / total berkas x 100%"],
        ["Data entry error", "0 kesalahan", "Cek sampling 10% data entry per bulan"],
    ])

    # Finance KPI
    pdf.sub_title("C. KPI DIVISI KEUANGAN & AKUNTING")
    pdf.kpi_table([
        ["Indikator", "Target", "Cara Ukur"],
        ["Waktu pencairan", "<= 1 hari kerja", "Tgl approval -> tgl transfer"],
        ["Laporan keuangan selesai", "Tgl 5 setiap bulan", "Cek tanggal penyelesaian laporan"],
        ["Selisih kas/bank", "Rp 0", "Rekonsiliasi harian"],
        ["Pajak tepat waktu", "100%", "Bukti setor dan SSP"],
        ["Pencatatan transaksi", "<= 1x24 jam", "Tgl transaksi -> tgl input sistem"],
    ])

    # Collection KPI
    pdf.sub_title("D. KPI DIVISI PENAGIHAN")
    pdf.kpi_table([
        ["Indikator", "Target", "Cara Ukur"],
        ["Tingkat kolektibilitas", ">= 95%", "Angsuran dibayar / total jatuh tempo x 100%"],
        ["Pengiriman reminder", "100%", "Cek log pengiriman WA/call"],
        ["NPL (Non Performing Loan)", "<= 5%", "Pinjaman macet / total pinjaman x 100%"],
        ["Follow up tepat waktu", "<= H+2", "Tgl jatuh tempo -> tgl follow up pertama"],
    ])

    # ---- PAGE 8-9: ALUR KERJA PINJAMAN ----
    pdf.add_page()
    pdf.section_title("ALUR KERJA PEMBERIAN PINJAMAN (5 TAHAP)", 4)
    pdf.body_text(
        "Proses pemberian pinjaman terdiri dari 5 tahap. Setiap tahap melibatkan "
        "divisi yang berbeda untuk menjaga kontrol internal (segregasi tugas). "
        "Tidak ada satu orang pun yang menangani seluruh proses sendirian."
    )

    stages = [
        ("TAHAP 1", "MARKETING", "Mencari & Mendaftarkan", GOLD, DARK_GRAY,
         "Marketing menemukan calon anggota atau anggota datang langsung.\n"
         "Marketing menjelaskan produk, syarat, dan bunga pinjaman.\n"
         "Calon anggota mengisi formulir pendaftaran dan menyerahkan dokumen awal.\n"
         "Marketing memeriksa kelengkapan dokumen dasar.\n"
         "Berkas dikirim ke Divisi Checking dengan checklist dokumen terisi."),
        ("TAHAP 2", "CHECKING", "Verifikasi & Validasi", MEDIUM_BLUE, WHITE,
         "Checking memverifikasi keaslian dokumen (KTP, KK, kontrak kerja, paspor).\n"
         "Menghubungi TKW via video call untuk konfirmasi data.\n"
         "Menghubungi pihak Taiwan (majikan/agen) untuk verifikasi pekerjaan.\n"
         "Validasi slip gaji atau rekening bank Taiwan.\n"
         "Jika lolos, membuat rekomendasi pinjaman untuk Manager.\n"
         "Jika tidak lolos, mengembalikan ke Marketing dengan catatan."),
        ("TAHAP 3", "MANAGER", "Approval Pinjaman", DARK_BLUE, WHITE,
         "Manager menerima rekomendasi dari Checking.\n"
         "Manager mengecek limit pinjaman dan riwayat anggota.\n"
         "Manager menyetujui (approve) atau menolak pengajuan.\n"
         "Berkas yang sudah di-approve diteruskan ke Divisi Keuangan."),
        ("TAHAP 4", "KEUANGAN", "Pencairan Dana", GREEN, WHITE,
         "Keuangan menyiapkan dana sesuai jumlah yang disetujui.\n"
         "Membuat surat perjanjian pinjaman yang ditandatangani anggota.\n"
         "Transfer dana ke rekening Taiwan (NTD) atau rekening Indonesia (IDR).\n"
         "Mencatat transaksi di buku kas dan sistem akuntansi.\n"
         "Menyimpan bukti transfer dan surat perjanjian."),
        ("TAHAP 5", "PENAGIHAN + KEUANGAN", "Pemantauan & Pembayaran", RED, WHITE,
         "Penagihan mencatat jadwal angsuran di sistem.\n"
         "H-5: Penagihan mengirim reminder WA ke anggota.\n"
         "H-0: Anggota membayar angsuran (transfer ke rekening koperasi).\n"
         "Keuangan mencatat angsuran masuk dan update saldo pinjaman.\n"
         "Jika terlambat: Penagihan follow up sesuai prosedur.\n"
         "Jika lunas: Keuangan membuat surat keterangan lunas."),
    ]

    for num, div, title, bg, tc, desc in stages:
        if pdf.get_y() > 230:
            pdf.add_page()
        y_before = pdf.get_y()

        # Stage number box
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*tuple(min(v + 30, 255) for v in bg))
        pdf.set_line_width(0.5)
        pdf.rect(15, y_before, 180, 14, style="DF")

        pdf.set_font("Noto", "B", 10)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(18, y_before + 1)
        pdf.cell(30, 5, num)
        pdf.set_font("Noto", "B", 12)
        pdf.set_xy(18, y_before + 6)
        pdf.cell(60, 6, f"{div} — {title}")
        pdf.set_font("Noto", "B", 9)
        pdf.set_xy(140, y_before + 3)
        pdf.cell(50, 5, f"PIC: {div}")

        pdf.set_y(y_before + 16)
        for line in desc.split("\n"):
            pdf.bullet(line.strip(), size=8)
        pdf.ln(3)

        # Arrow between stages
        if num != "TAHAP 5":
            y_arrow = pdf.get_y()
            pdf.set_draw_color(*GOLD)
            pdf.set_line_width(1)
            pdf.line(105, y_arrow, 105, y_arrow + 6)
            pdf.line(100, y_arrow + 3, 105, y_arrow + 6)
            pdf.line(110, y_arrow + 3, 105, y_arrow + 6)
            pdf.set_y(y_arrow + 8)

    # ---- PAGE 10: ALUR PENAGIHAN ----
    pdf.add_page()
    pdf.section_title("ALUR PENAGIHAN & FOLLOW UP", 5)
    pdf.body_text(
        "Divisi Penagihan bertanggung jawab menjaga tingkat angsuran tetap lancar. "
        "Berikut prosedur penagihan bertahap:"
    )

    collection_steps = [
        ("H-5", "PENGINGAT RAMAH", "Kirim WA: 'Hai Bu/Saudari, jangan lupa angsuran tanggal X ya. Terima kasih!'", LIGHT_BLUE, DARK_BLUE),
        ("H-1", "PENGINGAT + JUMLAH", "Kirim WA: 'Angsuran besok jatuh tempo, sebesar Rp X / NT$ X. Infokan jika ada kendala.'", LIGHT_BLUE, DARK_BLUE),
        ("H+1", "KONFIRMASI PEMBAYARAN", "Tanya: 'Apakah sudah transfer? Mohon kirim bukti transfer ya.'", LIGHT_BLUE, DARK_BLUE),
        ("H+3", "TEGURAN PERTAMA", "Telpon: tanyakan kendala, cari solusi (restrukturisasi jika perlu). Catat di sistem.", LIGHT_GRAY, RED),
        ("H+7", "TEGURAN KEDUA", "Telpon + WA: peringatan keterlambatan. Info denda keterlambatan.", LIGHT_GRAY, RED),
        ("H+14", "SURAT PERINGATAN (SP1)", "Kirim surat peringatan resmi. Laporkan ke Manager.", LIGHT_GRAY, RED),
        ("H+30+", "DISKUSI LANJUTAN / RESTRUK", "Manager + Penagihan bahas: restrukturisasi, perpanjangan, atau jalur hukum.", LIGHT_GRAY, RED),
    ]

    for time, action, detail, bg, tc in collection_steps:
        if pdf.get_y() > 260:
            pdf.add_page()
        y0 = pdf.get_y()
        # Time badge
        pdf.set_fill_color(*tc)
        pdf.set_draw_color(*MEDIUM_BLUE)
        pdf.set_line_width(0.3)
        pdf.rect(15, y0, 12, 8, style="F")
        pdf.set_font("Noto", "B", 7)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(15, y0 + 1.5)
        pdf.cell(12, 5, time, align="C")

        # Action + Detail
        pdf.set_xy(30, y0)
        pdf.set_font("Noto", "B", 9)
        pdf.set_text_color(*tc)
        pdf.cell(55, 4, action)
        pdf.set_font("Noto", "", 7.5)
        pdf.set_text_color(*DARK_GRAY)
        pdf.set_xy(30, y0 + 4)
        pdf.multi_cell(155, 4, detail)

        # Separator
        pdf.set_draw_color(*LIGHT_BLUE)
        pdf.set_y(max(pdf.get_y(), y0 + 10))
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

    # ---- PAGE 11: JADWAL RAPAT & PELAPORAN ----
    pdf.add_page()
    pdf.section_title("JADWAL RAPAT & PELAPORAN RUTIN", 6)

    pdf.sub_title("A. Rapat Koordinasi")
    pdf.kpi_table([
        ["Jenis Rapat", "Frekuensi", "Peserta", "Agenda"],
        ["Rapat Pagi (briefing)", "Setiap hari", "Semua divisi", "Target hari ini, masalah kemarin"],
        ["Rapat Mingguan", "Setiap Senin", "Semua divisi", "Review minggu lalu, target minggu ini"],
        ["Rapat Bulanan", "Awal bulan", "Semua divisi", "Evaluasi KPI, laporan keuangan"],
        ["Rapat Khusus", "Sesuai kebutuhan", "Divisi terkait + Manager", "Masalah khusus / anggota bermasalah"],
    ])

    pdf.sub_title("B. Jadwal Pelaporan")
    pdf.kpi_table([
        ["Laporan", "Penyusun", "Tujuan", "Batas Waktu"],
        ["Laporan Marketing", "Marketing", "Manager", "Setiap Senin"],
        ["Laporan Verifikasi", "Checking", "Manager", "Setiap hari selesai"],
        ["Laporan Keuangan", "Keuangan", "Manager", "Tgl 5 setiap bulan"],
        ["Laporan Penagihan", "Penagihan", "Manager", "Setiap Senin"],
        ["Laporan KPI Bulanan", "Semua Divisi", "Manager + Rapat", "Tgl 3 setiap bulan"],
    ])

    # ---- PAGE 12: PENGENDALIAN INTERNAL ----
    pdf.add_page()
    pdf.section_title("PENGENDALIAN INTERNAL & CEK SOP", 7)
    pdf.body_text(
        "Untuk menjaga kualitas kerja dan mencegah kesalahan, lakukan pengecekan "
        "berikut secara rutin. Centang () jika sudah dilakukan."
    )

    pdf.sub_title("A. Checklist Harian")
    checks_daily = [
        "Cek saldo kas/bank pagi hari (Keuangan)",
        "Cek pembayaran angsuran masuk hari sebelumnya (Penagihan)",
        "Input transaksi hari sebelumnya (Keuangan)",
        "Laporan singkat ke Manager (Semua Divisi)",
    ]
    for c in checks_daily:
        pdf.bullet(f"[ ] {c}")

    pdf.sub_title("B. Checklist Mingguan")
    checks_weekly = [
        "Rekonsiliasi kas/bank (Keuangan)",
        "Cek progres KPI mingguan (Semua Divisi)",
        "Cek anggota yang akan jatuh tempo minggu depan (Penagihan)",
        "Backup data sistem (Keuangan / Admin)",
        "Cek kelengkapan dokumen anggota baru (Checking)",
    ]
    for c in checks_weekly:
        pdf.bullet(f"[ ] {c}")

    pdf.sub_title("C. Checklist Bulanan")
    checks_monthly = [
        "Laporan keuangan lengkap (Neraca, Laba Rugi, Arus Kas)",
        "Evaluasi KPI semua divisi",
        "Rekonsiliasi bank bulanan",
        "Setor PPh 21 dan pajak lainnya",
        "Update daftar anggota aktif dan pinjaman",
        "Cek NPL (Non Performing Loan) ratio",
        "Rapat koordinasi bulanan",
        "Backup data full sistem",
    ]
    for c in checks_monthly:
        pdf.bullet(f"[ ] {c}")

    pdf.sub_title("D. Prinsip Pengendalian Internal")
    for p in [
        "Segregasi Tugas: Satu orang tidak boleh menangani seluruh proses transaksi.",
        "Dual Control: Setiap pencairan dana harus ditandatangani 2 orang (Keuangan + Manager).",
        "Dokumentasi: Setiap transaksi harus ada bukti (kwitansi, transfer slip, surat perjanjian).",
        "Audit Trail: Semua perubahan data terekam dengan user dan timestamp.",
        "Rekonsiliasi: Catatan koperasi harus cocok dengan catatan bank setiap bulan.",
        "Verifikasi Pihak Ketiga: Konfirmasi data anggota dengan pihak Taiwan (majikan/agen).",
    ]:
        pdf.bullet(p)

    # ---- PAGE 13: ISTILAH MANDARIN ----
    pdf.add_page()
    pdf.section_title("LAMPIRAN: ISTILAH MANDARIN-INDONESIA", 8)
    pdf.body_text(
        "Berikut istilah penting dalam Mandarin (Taiwan) yang sering digunakan "
        "dalam operasional koperasi TKW Taiwan."
    )

    pdf.kpi_table([
        ["Bahasa Indonesia", "English", "中文 (Mandarin Taiwan)"],
        ["Koperasi Simpan Pinjam", "Savings & Loan Cooperative", "儲蓄互助社 / 合作社"],
        ["Manager / Kepala", "Manager", "經理 (jīnglǐ)"],
        ["Marketing / Pemasaran", "Marketing", "行銷部 (xíngxiāo bù)"],
        ["Checking / Verifikasi", "Verification Dept.", "審核部 (shěnhé bù)"],
        ["Keuangan", "Finance Dept.", "財務部 (cáiwù bù)"],
        ["Akuntansi / Pembukuan", "Accounting", "會計 (kuàijì)"],
        ["Penagihan", "Collection Dept.", "催收部 (cuīshōu bù)"],
        ["Pinjaman", "Loan", "貸款 (dàikuǎn)"],
        ["Angsuran", "Installment", "分期付款 (fēnqī fùkuǎn)"],
        ["Bunga", "Interest", "利息 (lìxí)"],
        ["Simpanan / Tabungan", "Savings", "存款 (cúnkuǎn)"],
        ["Jatuh Tempo", "Due Date", "到期 (dàoqī)"],
        ["Pencairan Dana", "Disbursement", "撥款 (bōkuǎn)"],
        ["Slip Gaji", "Pay Slip", "薪資單 (xīnzī dān)"],
        ["Kontrak Kerja", "Work Contract", "勞動契約 (láodòng qìyuē)"],
        ["Paspor", "Passport", "護照 (hùzhào)"],
        ["Majikan / Pemberi Kerja", "Employer", "雇主 (gùzhǔ)"],
        ["Agen / Perantara", "Agent", "仲介 (zhòngjiè)"],
        ["Rekening Bank Taiwan", "Taiwan Bank Account", "台灣銀行帳戶"],
        ["Tanda Tangan", "Signature", "簽名 (qiānmíng)"],
        ["Denda", "Penalty / Fine", "罰款 (fákuǎn)"],
        ["Restrukturisasi", "Restructuring", "債務協商 (zhàiwù xiéshāng)"],
        ["Laporan Keuangan", "Financial Report", "財務報表 (cáiwù bàobiǎo)"],
        ["Laba Rugi", "Profit & Loss", "損益表 (sǔnyì biǎo)"],
        ["Neraca", "Balance Sheet", "資產負債表 (zīchǎn fùzhài biǎo)"],
        ["Pajak", "Tax", "稅 (shuì)"],
        ["Audit", "Audit", "稽核 (jīhé)"],
    ])

    # Save
    output_path = os.path.join(OUTPUT_DIR, "Buku_Pedoman_Organisasi_Koperasi_TKW.pdf")
    pdf.output(output_path)
    return output_path


# ============================================================
# MANDARIN VERSION CONTENT
# ============================================================
def build_mandarin():
    pdf = KoperasiPDF(
        lang="zh",
        title="組織架構與工作流程手冊",
        subtitle="台灣印尼移工儲蓄互助合作社"
    )
    pdf.set_margins(15, 10, 15)

    # ---- COVER PAGE ----
    pdf.add_page()
    pdf.ln(30)

    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(15, pdf.get_y(), 180, 3, style="F")
    pdf.ln(8)

    pdf.set_font("Noto", "B", 22)
    pdf.set_text_color(*DARK_BLUE)
    pdf.multi_cell(0, 12, "組織架構與\n工作流程手冊", align="C")
    pdf.ln(5)

    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.8)
    y = pdf.get_y()
    pdf.line(70, y, 140, y)
    pdf.ln(8)

    pdf.set_font("Noto", "B", 13)
    pdf.set_text_color(*MEDIUM_BLUE)
    pdf.cell(0, 8, "台灣印尼移工儲蓄互助合作社", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # People icons
    people_y = pdf.get_y()
    for i in range(7):
        px = 45 + i * 18
        pdf.set_draw_color(*DARK_BLUE)
        pdf.set_fill_color(*DARK_BLUE)
        pdf.circle(px, people_y, 4)
        pdf.line(px, people_y, px, people_y + 8)
        pdf.line(px - 4, people_y + 3, px + 4, people_y + 3)
        pdf.line(px, people_y + 8, px - 3, people_y + 13)
        pdf.line(px, people_y + 8, px + 3, people_y + 13)
    pdf.ln(20)

    pdf.set_fill_color(*LIGHT_BLUE)
    pdf.set_draw_color(*MEDIUM_BLUE)
    pdf.set_line_width(0.5)
    box_y = pdf.get_y()
    pdf.rect(30, box_y, 150, 30, style="DF")
    pdf.set_font("Noto", "", 9)
    pdf.set_text_color(*DARK_GRAY)
    pdf.set_xy(35, box_y + 4)
    pdf.cell(140, 5, "在台印尼移工專用", align="C")
    pdf.set_xy(35, box_y + 11)
    pdf.cell(140, 5, "部門工作指南 | 績效目標 | 貸款申請流程", align="C")
    pdf.set_xy(35, box_y + 18)
    pdf.cell(140, 5, "版本：2026年6月", align="C")
    pdf.ln(45)

    pdf.set_fill_color(*GOLD)
    pdf.rect(15, pdf.get_y(), 180, 2, style="F")

    # ---- TOC ----
    pdf.add_page()
    pdf.section_title("目錄")
    toc = [
        ("1", "組織架構與部門分工"),
        ("2", "各部門主要職責"),
        ("3", "績效指標目標 (KPI)"),
        ("4", "貸款申請流程 (5個步驟)"),
        ("5", "催收與跟進流程"),
        ("6", "會議與定期報告時程"),
        ("7", "內部控制與SOP檢查"),
        ("8", "附錄：用語對照表"),
    ]
    for num, title in toc:
        pdf.set_font("Noto", "B", 10)
        pdf.set_text_color(*MEDIUM_BLUE)
        pdf.cell(10, 7, num)
        pdf.set_font("Noto", "", 10)
        pdf.set_text_color(*DARK_GRAY)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*LIGHT_BLUE)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

    # ---- ORG STRUCTURE ----
    pdf.add_page()
    pdf.section_title("組織架構", 1)
    pdf.body_text(
        "以下是台灣印尼移工儲蓄互助合作社的組織架構圖。"
        "各部門依據職責分工合作，由經理統籌管理合作社的日常運營。"
    )

    # Manager box
    cx = 105
    box_w = 55
    box_h = 18
    mx = cx - box_w / 2
    my = pdf.get_y()
    pdf.draw_org_box(mx, my, box_w, box_h, "經理 MANAGER", "合作社負責人", DARK_BLUE, 1)
    mgr_bottom = my + box_h

    line_x = cx
    line_y1 = mgr_bottom
    line_y2 = line_y1 + 12
    pdf.set_draw_color(*DARK_BLUE)
    pdf.set_line_width(1.5)
    pdf.line(line_x, line_y1, line_x, line_y2)

    h_line_y = line_y2
    h_left = 20
    h_right = 190
    pdf.line(h_left, h_line_y, h_right, h_line_y)

    div_x_positions = [37, 75, 105, 135, 173]
    for dx in div_x_positions:
        pdf.set_draw_color(*DARK_BLUE)
        pdf.set_line_width(1.5)
        pdf.line(dx, h_line_y, dx, h_line_y + 10)

    div_data = [
        ("行銷部\nMARKETING", "市場開發", GOLD, DARK_GRAY, 3),
        ("審核行政部\nCHECKING & ADMIN", "文件審核", MEDIUM_BLUE, WHITE, 3),
        ("財務會計部\nFINANCE & ACC.", "撥款與帳務", GREEN, WHITE, 3),
        ("催收部\nCOLLECTION", "催收跟進", RED, WHITE, 3),
        ("秘書總務\nSECRETARY", "行政支援", ORANGE, WHITE, 2),
    ]

    div_w = 32
    div_h = 42
    div_start_y = h_line_y + 10

    for i, (title, desc, bg, tc, ppl) in enumerate(div_data):
        dx = div_x_positions[i] - div_w / 2
        pdf.draw_org_box(dx, div_start_y, div_w, div_h, title, "", bg, ppl)
        pdf.set_font("Noto", "", 6)
        pdf.set_text_color(*DARK_GRAY)
        pdf.set_xy(dx, div_start_y + div_h + 2)
        pdf.cell(div_w, 4, desc, align="C")

    pdf.set_y(div_start_y + div_h + 12)

    pdf.sub_title("職責分工原則")
    pdf.body_text(
        "經理：領導合作社所有業務，做出戰略決策，批准超過限額的貸款，並對會員大會負責。\n\n"
        "秘書總務：協助會議行政、重要文件歸檔、辦公室後勤管理。\n\n"
        "各部門獨立運作但相互聯繫。實施職責分離原則，防止錯誤和權力濫用。"
    )

    # ---- TUGAS POKOK ----
    pdf.add_page()
    pdf.section_title("各部門主要職責", 2)

    pdf.sub_title("A. 行銷部 (MARKETING)")
    pdf.body_text("負責尋找會員並向台灣的印尼移工推廣合作社。")
    for b in [
        "通過社群媒體、群組和推薦方式宣傳合作社。",
        "向潛在會員說明貸款的條件和條款。",
        "收集潛在會員的初步資料（申請表、身份證、工作合同）。",
        "維持與活躍會員的良好關係（會員關懷）。",
        "將申請轉交審核部進行後續驗證。",
    ]:
        pdf.bullet(b)

    pdf.sub_title("B. 審核行政部 (CHECKING & ADMINISTRATION)")
    pdf.body_text("負責驗證申請文件的完整性和真實性。")
    for b in [
        "檢查身份證、戶口名簿、台灣工作合同和護照的真實性。",
        "通過視訊通話與移工及台灣僱主/仲介進行資料確認。",
        "驗證最近3個月的台灣薪資單或銀行對帳單。",
        "將會員資料輸入系統（姓名、地址、台灣銀行帳戶等）。",
        "準備貸款申請文件，轉交財務部處理。",
    ]:
        pdf.bullet(b)

    pdf.sub_title("C. 財務會計部 (FINANCE & ACCOUNTING)")
    pdf.body_text("負責撥款並記錄所有財務交易。")
    for b in [
        "根據經理批准的金額準備撥款資金。",
        "將資金轉入移工的台灣或印尼銀行帳戶（依協議而定）。",
        "記錄所有交易：存款收入、貸款撥款、分期付款、費用。",
        "編制月度財務報表（資產負債表、損益表、現金流量表）。",
        "每月進行銀行對帳。",
        "按時繳納所得稅及其他稅款。",
    ]:
        pdf.bullet(b)

    pdf.sub_title("D. 催收部 (COLLECTION)")
    pdf.body_text("負責收取分期付款和跟進逾期款項。")
    for b in [
        "在到期日前3-5天通過Line/電話提醒會員。",
        "監控每日/每週/每月的付款情況。",
        "跟進逾期會員（階段：提醒 → 警告 → 拜訪）。",
        "記錄催收結果（聯繫日期、回應、付款承諾）。",
        "向經理報告有問題的會員以採取進一步行動。",
    ]:
        pdf.bullet(b)

    # ---- KPI ----
    pdf.add_page()
    pdf.section_title("績效指標目標 (KPI)", 3)
    pdf.body_text(
        "各部門每月需達成以下績效目標。KPI於每月初的協調會議進行評估，"
        "並可根據合作社實際營運狀況調整。"
    )

    pdf.sub_title("A. 行銷部 KPI")
    pdf.kpi_table([
        ["指標", "目標", "衡量方式"],
        ["新會員人數", "每月>=15人", "計算進入審核階段的會員數"],
        ["轉換率", ">=60%", "完成撥款人數/申請人數x100%"],
        ["活躍會員聯繫率", ">=80%", "已聯繫活躍會員/總活躍會員x100%"],
        ["會員投訴", "每月<5件", "記錄收到的投訴"],
    ])

    pdf.sub_title("B. 審核行政部 KPI")
    pdf.kpi_table([
        ["指標", "目標", "衡量方式"],
        ["審核時間", "<=3個工作日", "收件日->審核完成日"],
        ["審核準確率", ">=98%", "正確文件/總文件x100%"],
        ["文件完整率", ">=90%", "完整文件/總文件x100%"],
        ["資料輸入錯誤", "0錯誤", "每月抽查10%資料"],
    ])

    pdf.sub_title("C. 財務會計部 KPI")
    pdf.kpi_table([
        ["指標", "目標", "衡量方式"],
        ["撥款時間", "<=1個工作日", "批准日->轉帳日"],
        ["財務報表完成日", "每月5日", "檢查報表完成日期"],
        ["現金/銀行差額", "NT$0", "每日對帳"],
        ["按時繳稅", "100%", "繳稅憑證"],
        ["交易記錄時效", "<=24小時", "交易日期->輸入系統日期"],
    ])

    pdf.sub_title("D. 催收部 KPI")
    pdf.kpi_table([
        ["指標", "目標", "衡量方式"],
        ["回收率", ">=95%", "已付分期/到期總額x100%"],
        ["提醒發送率", "100%", "檢查Line/電話發送記錄"],
        ["逾期貸款率", "<=5%", "逾期貸款/總貸款x100%"],
        ["跟進時效", "<=逾期2天", "到期日->首次跟進日"],
    ])

    # ---- ALUR PINJAMAN ----
    pdf.add_page()
    pdf.section_title("貸款申請流程 (5個步驟)", 4)
    pdf.body_text(
        "貸款申請分為5個步驟，每個步驟涉及不同部門，以維持內部控制（職責分離原則）。"
        "沒有任何一個人可以單獨完成整個流程。"
    )

    stages = [
        ("步驟 1", "行銷部", "尋找與登記", GOLD, DARK_GRAY,
         "行銷人員尋找潛在會員，或會員親自前來申請。\n"
         "行銷人員說明貸款產品、條件和利率。\n"
         "申請人填寫申請表並提交基本文件。\n"
         "行銷人員檢查基本文件是否齊全。\n"
         "文件連同檢查清單轉交審核部。"),
        ("步驟 2", "審核部", "審核與驗證", MEDIUM_BLUE, WHITE,
         "審核部驗證文件真偽（身份證、戶口名簿、工作合同、護照）。\n"
         "通過視訊通話與移工確認資料。\n"
         "聯繫台灣僱主或仲介確認工作狀況。\n"
         "驗證薪資單或台灣銀行對帳單。\n"
         "如通過，撰寫貸款建議書提交經理。\n"
         "如未通過，退還行銷部並附註原因。"),
        ("步驟 3", "經理", "批准貸款", DARK_BLUE, WHITE,
         "經理收到審核部的建議書。\n"
         "經理檢查貸款限額和會員記錄。\n"
         "經理批准或拒絕申請。\n"
         "已批准的申請文件轉交財務部。"),
        ("步驟 4", "財務部", "撥款", GREEN, WHITE,
         "財務部根據批准金額準備資金。\n"
         "製作貸款協議書，由會員簽署。\n"
         "將資金轉入會員的台灣（新台幣）或印尼（印尼盾）帳戶。\n"
         "在現金帳和會計系統中記錄交易。\n"
         "保存轉帳憑證和貸款協議書。"),
        ("步驟 5", "催收部 + 財務部", "監控與還款", RED, WHITE,
         "催收部在系統中記錄分期付款時間表。\n"
         "到期前5天：催收部發送Line提醒。\n"
         "到期日：會員支付分期款項（轉帳至合作社帳戶）。\n"
         "財務部記錄收到的分期款項並更新貸款餘額。\n"
         "如逾期：催收部按程序跟進。\n"
         "如還清：財務部開具清償證明。"),
    ]

    for num, div, title, bg, tc, desc in stages:
        if pdf.get_y() > 230:
            pdf.add_page()
        y_before = pdf.get_y()

        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*tuple(min(v + 30, 255) for v in bg))
        pdf.set_line_width(0.5)
        pdf.rect(15, y_before, 180, 14, style="DF")

        pdf.set_font("Noto", "B", 10)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(18, y_before + 1)
        pdf.cell(30, 5, num)
        pdf.set_font("Noto", "B", 12)
        pdf.set_xy(18, y_before + 6)
        pdf.cell(60, 6, f"{div} — {title}")
        pdf.set_font("Noto", "B", 9)
        pdf.set_xy(140, y_before + 3)
        pdf.cell(50, 5, f"負責: {div}")

        pdf.set_y(y_before + 16)
        for line in desc.split("\n"):
            pdf.bullet(line.strip(), size=8)
        pdf.ln(3)

        if num != "步驟 5":
            y_arrow = pdf.get_y()
            pdf.set_draw_color(*GOLD)
            pdf.set_line_width(1)
            pdf.line(105, y_arrow, 105, y_arrow + 6)
            pdf.line(100, y_arrow + 3, 105, y_arrow + 6)
            pdf.line(110, y_arrow + 3, 105, y_arrow + 6)
            pdf.set_y(y_arrow + 8)

    # ---- ALUR PENAGIHAN ----
    pdf.add_page()
    pdf.section_title("催收與跟進流程", 5)
    pdf.body_text(
        "催收部負責確保分期付款按時繳納。以下是分階段催收程序："
    )

    collection_steps = [
        ("到期前5天", "溫馨提醒", "發送Line：'您好，請記得於X日繳納分期款項，謝謝！'", LIGHT_BLUE, DARK_BLUE),
        ("到期前1天", "提醒+金額", "發送Line：'明天是分期繳款日，金額為NT$X/印尼盾X，如有問題請告知。'", LIGHT_BLUE, DARK_BLUE),
        ("逾期1天", "確認付款", "詢問：'請問是否已轉帳？請提供轉帳憑證。'", LIGHT_BLUE, DARK_BLUE),
        ("逾期3天", "首次警告", "致電：詢問原因，尋找解決方案（必要時協商債務）。記錄於系統。", LIGHT_GRAY, RED),
        ("逾期7天", "第二次警告", "電話+Line：逾期警告，說明逾期罰款。", LIGHT_GRAY, RED),
        ("逾期14天", "正式警告函", "發送正式警告函，報告經理。", LIGHT_GRAY, RED),
        ("逾期30天+", "後續討論/協商", "經理+催收部討論：債務協商、展期或法律途徑。", LIGHT_GRAY, RED),
    ]

    for time, action, detail, bg, tc in collection_steps:
        if pdf.get_y() > 260:
            pdf.add_page()
        y0 = pdf.get_y()
        pdf.set_fill_color(*tc)
        if isinstance(tc, tuple) and len(tc) == 3:
            pdf.set_fill_color(*tc)
        pdf.set_draw_color(*MEDIUM_BLUE)
        pdf.set_line_width(0.3)
        pdf.rect(15, y0, 18, 8, style="F")
        pdf.set_font("Noto", "B", 6)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(15, y0 + 1.5)
        pdf.cell(18, 5, time, align="C")

        pdf.set_xy(36, y0)
        pdf.set_font("Noto", "B", 9)
        pdf.set_text_color(*tc)
        pdf.cell(50, 4, action)
        pdf.set_font("Noto", "", 7.5)
        pdf.set_text_color(*DARK_GRAY)
        pdf.set_xy(36, y0 + 4)
        pdf.multi_cell(149, 4, detail)

        pdf.set_draw_color(*LIGHT_BLUE)
        pdf.set_y(max(pdf.get_y(), y0 + 10))
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

    # ---- JADWAL ----
    pdf.add_page()
    pdf.section_title("會議與定期報告時程", 6)

    pdf.sub_title("A. 協調會議")
    pdf.kpi_table([
        ["會議類型", "頻率", "參加者", "議程"],
        ["晨會", "每天", "所有部門", "今日目標，昨日問題"],
        ["週會", "每週一", "所有部門", "上週檢討，本週目標"],
        ["月會", "月初", "所有部門", "KPI評估，財務報告"],
        ["臨時會議", "視需要", "相關部門+經理", "特殊問題/問題會員"],
    ])

    pdf.sub_title("B. 報告時程")
    pdf.kpi_table([
        ["報告名稱", "編製人", "提交對象", "截止時間"],
        ["行銷報告", "行銷部", "經理", "每週一"],
        ["審核報告", "審核部", "經理", "每天完成時"],
        ["財務報告", "財務部", "經理", "每月5日"],
        ["催收報告", "催收部", "經理", "每週一"],
        ["月度KPI報告", "所有部門", "經理+會議", "每月3日"],
    ])

    # ---- INTERNAL CONTROL ----
    pdf.add_page()
    pdf.section_title("內部控制與SOP檢查", 7)
    pdf.body_text(
        "為確保工作品質並防止錯誤，請定期進行以下檢查。完成後請打勾。"
    )

    pdf.sub_title("A. 每日檢查清單")
    for c in [
        "早上檢查現金/銀行餘額（財務部）",
        "檢查前一日分期付款入帳情況（催收部）",
        "記錄前一日交易（財務部）",
        "向經理提交簡報（所有部門）",
    ]:
        pdf.bullet(f"[ ] {c}")

    pdf.sub_title("B. 每週檢查清單")
    for c in [
        "現金/銀行對帳（財務部）",
        "檢查當週KPI進度（所有部門）",
        "檢查下週到期的會員（催收部）",
        "系統資料備份（財務部/行政）",
        "檢查新會員文件完整性（審核部）",
    ]:
        pdf.bullet(f"[ ] {c}")

    pdf.sub_title("C. 每月檢查清單")
    for c in [
        "完成財務報表（資產負債表、損益表、現金流量表）",
        "評估所有部門KPI",
        "月度銀行對帳",
        "繳納所得稅及其他稅款",
        "更新活躍會員和貸款清單",
        "檢查逾期貸款率",
        "月度協調會議",
        "完整系統資料備份",
    ]:
        pdf.bullet(f"[ ] {c}")

    pdf.sub_title("D. 內部控制原則")
    for p in [
        "職責分離：同一人不得處理整個交易流程。",
        "雙重控制：每次撥款必須由2人簽署（財務+經理）。",
        "文件化：每筆交易必須有憑證（收據、轉帳單、協議書）。",
        "稽核軌跡：所有資料更改需記錄使用者和時間。",
        "對帳：合作社記錄必須每月與銀行記錄一致。",
        "第三方驗證：透過台灣僱主/仲介確認會員資料。",
    ]:
        pdf.bullet(p)

    # ---- APPENDIX ----
    pdf.add_page()
    pdf.section_title("附錄：用語對照表", 8)
    pdf.body_text(
        "以下為合作社營運中常用的中印尼英三語對照表。"
    )

    pdf.kpi_table([
        ["中文 (繁體)", "Bahasa Indonesia", "English"],
        ["儲蓄互助社 / 合作社", "Koperasi Simpan Pinjam", "Savings & Loan Cooperative"],
        ["經理", "Manager / Kepala", "Manager"],
        ["行銷部", "Divisi Marketing", "Marketing Dept."],
        ["審核部", "Divisi Checking", "Verification Dept."],
        ["財務部", "Divisi Keuangan", "Finance Dept."],
        ["會計", "Akuntansi", "Accounting"],
        ["催收部", "Divisi Penagihan", "Collection Dept."],
        ["貸款", "Pinjaman", "Loan"],
        ["分期付款", "Angsuran", "Installment"],
        ["利息", "Bunga", "Interest"],
        ["存款", "Simpanan / Tabungan", "Savings"],
        ["到期", "Jatuh Tempo", "Due Date"],
        ["撥款", "Pencairan Dana", "Disbursement"],
        ["薪資單", "Slip Gaji", "Pay Slip"],
        ["勞動契約", "Kontrak Kerja", "Work Contract"],
        ["護照", "Paspor", "Passport"],
        ["雇主", "Majikan / Pemberi Kerja", "Employer"],
        ["仲介", "Agen / Perantara", "Agent"],
        ["台灣銀行帳戶", "Rekening Bank Taiwan", "Taiwan Bank Account"],
        ["簽名", "Tanda Tangan", "Signature"],
        ["罰款", "Denda", "Penalty / Fine"],
        ["債務協商", "Restrukturisasi", "Restructuring"],
        ["財務報表", "Laporan Keuangan", "Financial Report"],
        ["損益表", "Laba Rugi", "Profit & Loss"],
        ["資產負債表", "Neraca", "Balance Sheet"],
        ["稅", "Pajak", "Tax"],
        ["稽核", "Audit", "Audit"],
    ])

    output_path = os.path.join(OUTPUT_DIR, "組織架構與工作流程手冊_合作社.pdf")
    pdf.output(output_path)
    return output_path


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("Generating Indonesia version...")
    id_path = build_indonesia()
    print(f"OK: {id_path}")

    print("Generating Mandarin version...")
    zh_path = build_mandarin()
    print(f"OK: {zh_path}")

    print("\nDone! Both PDFs generated.")
    print(f"  ID: {id_path}")
    print(f"  ZH: {zh_path}")
