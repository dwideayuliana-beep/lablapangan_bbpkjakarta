import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import io

# ==============================
# Config
# ==============================
st.set_page_config(page_title="Dashboard Pengembangan Lab Lapangan SDM BBPK Jakarta", layout="wide")

# Assets
LOGO = "e78757e1-65d0-4688-aecb-fe70f9ca4fe2.png"
DATA_FILE = "Dashboard_MultiKlaster_BBPK_Final.xlsx"
DATA_SHEET = "Dashboard_Interaktif"

# Splash / Home
if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    st.markdown(f"""
    <div style="text-align:center;padding:30px;background-color:white;border-radius:8px;">
        <img src="{LOGO}" width="200" style="margin-bottom:10px;">
        <h1 style="color:#004B87;margin:5px 0;">Selamat Datang di Dashboard Pengembangan SDM BBPK Jakarta</h1>
        <h3 style="color:#004B87;margin:5px 0;font-weight:400;">"Mendukung SDM yang Kompeten, Mandiri, dan Berkeadilan"</h3>
        <p style="font-size:16px;color:#333;margin-top:12px;">🌿 Bersama kita wujudkan insan pembelajar yang unggul, adaptif, dan berintegritas 🌿</p>
        <div style="margin-top:20px;">
            <button onclick="window.location.href='#' " style="background-color:#004B87;color:white;padding:10px 18px;border-radius:6px;border:none;font-size:16px;" id="enter-btn">➡️ Masuk ke Dashboard</button>
        </div>
    </div>
    <script>
    const btn = window.parent.document.getElementById("enter-btn");
    if (btn) { btn.onclick = function() { window.parent.location.href = window.parent.location.href + "?__page=dashboard"; } }
    </script>
    """, unsafe_allow_html=True)

    # Button fallback (Streamlit native)
    if st.button("➡️ Masuk ke Dashboard"):
        st.session_state.page = "dashboard"
    st.stop()

# ==============================
# Load data
# ==============================
@st.cache_data
def load_data(path=DATA_FILE, sheet=DATA_SHEET):
    df = pd.read_excel(path, sheet_name=sheet)
    # Identify P columns
    nilai_cols = [c for c in df.columns if str(c).strip().upper().startswith("P")]
    # Ensure Klaster & Nama columns
    if "Klaster" not in df.columns:
        df["Klaster"] = "Klaster1"
    if "Nama" not in df.columns:
        # try to infer from sheet if single-name layout: if there is a "B2" like structure not applicable here; default to index
        df["Nama"] = df.index.astype(str)
    # If the sheet is a per-individual snapshot (only one row per name) it should still work.
    df["Rata-rata"] = df[nilai_cols].mean(axis=1)
    def kategori(x):
        if x < 3: return "Belum/Akan Berkembang"
        elif x < 4: return "Sedang Berkembang"
        else: return "Sudah/Sangat Optimal"
    df["Kategori"] = df["Rata-rata"].apply(kategori)
    return df, nilai_cols

df, nilai_cols = load_data()

# ==============================
# Sidebar filters
# ==============================
st.sidebar.header("Filter Pilihan")
klaster_list = sorted(df["Klaster"].unique())
selected_klaster = st.sidebar.selectbox("Pilih Klaster", klaster_list)

nama_list = sorted(df[df["Klaster"] == selected_klaster]["Nama"].unique())
selected_nama = st.sidebar.selectbox("Pilih Nama Individu", nama_list)

# ==============================
# Fetch individual's data
# ==============================
person = df[(df["Klaster"] == selected_klaster) & (df["Nama"] == selected_nama)].iloc[0]
values = person[nilai_cols].astype(float).values.tolist()

# ==============================
# Radar plot
# ==============================
def make_radar(categories, values, title):
    N = len(categories)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    vals = values + values[:1]
    angs = angles + angles[:1]
    fig, ax = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))
    ax.plot(angs, vals, linewidth=2, linestyle='solid', color='#004B87')
    ax.fill(angs, vals, alpha=0.25, color='#5DADE2')
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_yticks([1,2,3,4,5])
    ax.set_ylim(0,5)
    ax.set_title(title, size=12, color='#004B87', pad=20)
    return fig

fig = make_radar(nilai_cols, values.copy(), f"Radar Kompetensi – {selected_nama} ({selected_klaster})")

# ==============================
# Dashboard layout
# ==============================
col1, col2 = st.columns([2,1])
with col1:
    st.pyplot(fig)
with col2:
    st.markdown("### 🔎 Ringkasan Kompetensi")
    rata = float(np.mean(values))
    st.metric("Rata-rata Kompetensi", f"{rata:.2f}")
    kategori = "Belum/Akan Berkembang" if rata < 3 else ("Sedang Berkembang" if rata < 4 else "Sudah/Sangat Optimal")
    warna = "🔴" if kategori.startswith("Belum") else ("🟡" if kategori.startswith("Sedang") else "🟢")
    st.write(f"{warna} **Kategori:** {kategori}")
    st.write("• Kompetensi tertinggi:", nilai_cols[int(np.argmax(values))])
    st.write("• Kompetensi terendah:", nilai_cols[int(np.argmin(values))])
    st.markdown("---")
    st.markdown("### 💡 Rekomendasi Pengembangan")
    if kategori == "Belum/Akan Berkembang":
        st.write("- Fokus pada microlearning & coaching.\n- Diperkuat dengan mentoring lintas klaster.")
    elif kategori == "Sedang Berkembang":
        st.write("- Pertahankan praktik baik.\n- Didorong kolaborasi & refleksi tim.")
    else:
        st.write("- Sudah sangat optimal.\n- Siap menjadi fasilitator Learning Cell & mentor di BBPK Jakarta.")

# ==============================
# PDF export with header & footer
# ==============================
def export_pdf(nama, klaster, categories, values, avg, kategori, fig):
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        # Page 1 - radar with header/footer text
        fig.suptitle("PROFIL KOMPETENSI SDM BBPK JAKARTA", fontsize=14, color="#004B87", weight="bold", y=1.02)
        fig.text(0.5, 0.01, f"Nama: {nama}   |   Klaster: {klaster}   |   Rata-rata: {avg:.2f}   |   Kategori: {kategori}", ha="center", fontsize=9, color="#004B87")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
        # Page 2 - insight and recommendations with header and footer
        fig2 = plt.figure(figsize=(8.27, 11.69))
        plt.axis("off")
        header = "BBPK Jakarta – Balai Besar Pelatihan Kesehatan"
        footer = "Learning Transformation for a Healthier Nation"
        teks = f"PROFIL PENGEMBANGAN KOMPETENSI\n\nNama: {nama}\nKlaster: {klaster}\nRata-rata Kompetensi: {avg:.2f}\nKategori: {kategori}\n\nREKOMENDASI PENGEMBANGAN:\n"
        if kategori == "Belum/Akan Berkembang":
            teks += "- Pendampingan intensif\n- Microlearning lintas klaster\n- Coaching terarah\n"
        elif kategori == "Sedang Berkembang":
            teks += "- Penguatan peer learning\n- Simulasi & refleksi kolaboratif\n"
        else:
            teks += "- Siap menjadi role model & fasilitator Learning Cell\n- Dokumentasi best practice\n"
        plt.text(0.05, 0.92, header, fontsize=13, color="#004B87", weight="bold", va="top")
        plt.text(0.05, 0.78, teks, fontsize=11, va="top")
        plt.text(0.5, 0.05, footer, fontsize=10, color="#666666", ha="center", va="bottom", style="italic")
        pdf.savefig(bbox_inches="tight")
        plt.close(fig2)
    buffer.seek(0)
    return buffer

st.markdown("---")
if st.button("🖨️ Generate PDF Profil Individu"):
    pdf_file = export_pdf(selected_nama, selected_klaster, nilai_cols, values.copy(), rata, kategori, fig)
    st.download_button("⬇️ Download PDF Profil", data=pdf_file, file_name=f"BBPKJKT_{selected_klaster}_{selected_nama.replace(' ','_')}.pdf", mime="application/pdf")

# Footer
st.markdown("""
---
🩺 **BBPK Jakarta – Learning Transformation for a Healthier Nation**  
*Prototype Dashboard Streamlit © 2025*
""")
