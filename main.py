import streamlit as st
import pandas as pd
import numpy as np

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Analisis Perbandingan Metode SAW dan WP untuk Seleksi Hosting", layout="wide")

st.title("Analisis Perbandingan Metode SAW dan WP untuk Seleksi Hosting")
st.markdown("""
Sistem ini dibangun untuk mengimplementasikan dan membandingkan dua metode **Multi-Attribute Decision Making (MADM)**, yaitu:
1.  **Simple Additive Weighting (SAW)**
2.  **Weighted Product (WP)**
""")

# --- 1. DEFINISI KRITERIA & BOBOT ---
# Bobot ini tetap merupakan bobot kepentingan relatif antar kriteria (0-1).
CRITERIA_CONFIG = {
    "C1": {"name": "Harga Bulanan (C1)", "weight": 0.3, "attr": "cost"}, # C1 adalah kriteria biaya (cost)
    "C2": {"name": "Kapasitas Penyimpanan (C2)", "weight": 0.2, "attr": "benefit"},
    "C3": {"name": "Bandwidth (C3)", "weight": 0.2, "attr": "benefit"},
    "C4": {"name": "Uptime (C4)", "weight": 0.15, "attr": "benefit"},
    "C5": {"name": "Fitur (C5)", "weight": 0.15, "attr": "benefit"}
}

# --- 2. DATA AWAL (DEFAULT) ---
# Data sampel disesuaikan agar cocok dengan kriteria baru dan nilai dari gambar.
default_data = {
    "Alternatif": ["A1", "A2", "A3", "A4", "A5"],
    # Harga dalam Rupiah (Rp) - Hapus tanda titik untuk perhitungan numerik
    "Harga Bulanan (C1)": [8000, 10000, 13000, 15000, 15000],
    # Kapasitas Penyimpanan dalam GB
    "Kapasitas Penyimpanan (C2)": [5, 1, 20, 1, 1],
    # Bandwidth dalam GB (Gunakan angka 100000 untuk representasi Unlimited di fungsi fuzzifikasi)
    "Bandwidth (C3)": [100000, 100000, 100, 100000, 100000],
    # Uptime dalam Persen (%)
    "Uptime (C4)": [99.90, 99.98, 99.90, 99.90, 99.90],
    # Skor fitur 1-5
    "Fitur (C5)": [4, 3, 4, 4, 4]
}

# --- 3. FUNGSI LOGIKA (BACKEND PERHITUNGAN) ---

def run_fuzzification(df):
    """Mengubah data mentah menjadi nilai Fuzzy (skor 1-5) sesuai tabel sub-kriteria gambar"""
    df_fuzzy = df.copy()
    
    # Logika C1: Harga Bulanan (Cost)
    def fuzz_c1(val):
        if val <= 10000: return 5
        elif val <= 20000: return 4
        elif val <= 40000: return 3
        elif val <= 80000: return 2
        else: return 1

    # Logika C2: Kapasitas Penyimpanan (Benefit)
    def fuzz_c2(val):
        if val > 10: return 5 # 11-20 GB atau lebih
        elif val > 4: return 4 # 5-10 GB
        elif val > 1: return 3 # 2-4 GB
        elif val > 0.5: return 2 # 0.6-1 GB
        else: return 1 # 0-0.5 GB
        
    # Logika C3: Bandwidth (Benefit)
    def fuzz_c3(val):
        if val > 1000: return 5 # Unlimited (kita pakai 100000 di data)
        elif val > 100: return 4 # 101-1000 GB
        elif val > 50: return 3 # 51-100 GB
        elif val > 10: return 2 # 11-50 GB
        else: return 1 # 0-10 GB

    # Logika C4: Uptime (Benefit)
    def fuzz_c4(val):
        if val >= 99.98: return 5
        elif val >= 99.95: return 4
        elif val >= 99.92: return 3
        elif val >= 99.90: return 2
        else: return 1

    # Logika C5: Fitur (Skor sudah dalam 1-5 di data awal, tidak perlu fuzzifikasi ulang)
    def fuzz_c5(val):
        return val

    # Terapkan fungsi ke kolom
    df_fuzzy["Harga Bulanan (C1)"] = df["Harga Bulanan (C1)"].apply(fuzz_c1)
    df_fuzzy["Kapasitas Penyimpanan (C2)"] = df["Kapasitas Penyimpanan (C2)"].apply(fuzz_c2)
    df_fuzzy["Bandwidth (C3)"] = df["Bandwidth (C3)"].apply(fuzz_c3)
    df_fuzzy["Uptime (C4)"] = df["Uptime (C4)"].apply(fuzz_c4)
    df_fuzzy["Fitur (C5)"] = df["Fitur (C5)"].apply(fuzz_c5)
    
    return df_fuzzy

# --- 4. INTERFACE INPUT DATA ---

with st.expander("Input Data Alternatif (Edit di sini!)", expanded=True):
    st.info("Dapat menambah tabel, mengedit tabel, dan menghapus tabel. Klik 'Hitung Ranking' untuk melihat hasil kalkulasi ulang.")
    df_input = pd.DataFrame(default_data)
    edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

btn_hitung = st.button("Hitung Ranking")

# --- 5. PROSES KALKULASI ---

if btn_hitung:
    st.divider()
    
    # A. PRE-PROCESSING
    alternatives = edited_df["Alternatif"].values
    data_only = edited_df.drop(columns=["Alternatif"])
    
    # Lakukan Fuzzifikasi (konversi data mentah ke skor 1-5)
    fuzzy_df = run_fuzzification(data_only)
    fuzzy_df.index = alternatives 
    
    # Ambil list bobot urut (bobot kepentingan antar kriteria)
    weights = [conf["weight"] for key, conf in CRITERIA_CONFIG.items()]
    attrs = [conf["attr"] for key, conf in CRITERIA_CONFIG.items()] # Tambahkan atribut benefit/cost

    # Tampilkan Hasil Fuzzifikasi
    st.subheader("1. Matriks Hasil Fuzzifikasi (Skor 1-5)")
    st.dataframe(fuzzy_df)

    # --- TAB UNTUK MASING-MASING METODE ---
    tab_saw, tab_wp, tab_result = st.tabs(["Metode SAW", "Metode WP", "Ranking Akhir"])

    # === METODE SAW ===
    with tab_saw:
        st.write("### Perhitungan SAW")
        
        # 1. Normalisasi SAW (mempertimbangkan benefit/cost)
        max_vals = fuzzy_df.max()
        min_vals = fuzzy_df.min()
        
        norm_saw = fuzzy_df.copy()
        for col, attr in zip(norm_saw.columns, attrs):
            if attr == "benefit":
                norm_saw[col] = norm_saw[col] / max_vals[col]
            else: # attr == "cost"
                norm_saw[col] = min_vals[col] / norm_saw[col]

        st.write("**a. Tabel Normalisasi (R) - (10 Digit Desimal):**")
        st.dataframe(norm_saw.style.format("{:.10f}"))
        
        # 2. Perankingan
        saw_final = norm_saw.dot(weights) 
        
        st.write("**b. Nilai Preferensi (V) - (10 Digit Desimal):**")
        df_saw_res = pd.DataFrame(saw_final, columns=["Nilai SAW"])
        st.dataframe(df_saw_res.style.format("{:.10f}"))

    # === METODE WP ===
    with tab_wp:
        st.write("### Perhitungan WP")
        
        # WP normalisasi bobot sudah dilakukan di definisi awal (sum(weights) == 1)
        # 1. Hitung Vektor S (Perkalian Pangkat)
        vector_s = []
        col_names = list(fuzzy_df.columns)
        for idx, row in fuzzy_df.iterrows():
            s_val = 1.0
            for i in range(len(col_names)):
                val = row[col_names[i]]
                w = weights[i]
                s_val = s_val * (val ** w)
            vector_s.append(s_val)
            
        df_wp_s = pd.DataFrame({"Vector S": vector_s}, index=alternatives)
        total_s = sum(vector_s)
        
        st.write("**a. Vector S (Perkalian Pangkat) - (10 Digit Desimal):**")
        st.dataframe(df_wp_s.style.format("{:.10f}"))
        st.write(f"**Total S:** {total_s:.10f}")
        
        # 2. Vector V (Nilai Akhir)
        df_wp_v = df_wp_s / total_s
        df_wp_v.columns = ["Nilai WP"]
        st.write("**b. Vector V (Nilai Akhir) - (10 Digit Desimal):**")
        st.dataframe(df_wp_v.style.format("{:.10f}"))

    # === TAB HASIL AKHIR ===
    with tab_result:
        st.header("Perbandingan Hasil Ranking")
        
        # Gabungkan semua hasil
        final_df = pd.DataFrame(index=alternatives)
        final_df["SAW Score"] = df_saw_res["Nilai SAW"]
        final_df["SAW Rank"] = final_df["SAW Score"].rank(ascending=False).astype(int)
        
        final_df["WP Score"] = df_wp_v["Nilai WP"]
        final_df["WP Rank"] = final_df["WP Score"].rank(ascending=False).astype(int)
        
        # Tampilkan tabel gabungan
        st.dataframe(final_df.style.format({
            "SAW Score": "{:.10f}",
            "WP Score": "{:.10f}"
        }))
        
        # Kesimpulan Teks
        best_saw = final_df.sort_values("SAW Rank").index[0]
        best_wp = final_df.sort_values("WP Rank").index[0]
        
        st.success(f"""
        **Kesimpulan Rekomendasi:**
        * Menurut **SAW**: {best_saw}
        * Menurut **WP**: {best_wp}
        """)

else:
    st.warning("Silakan edit data di atas (jika perlu), lalu klik tombol 'Hitung Ranking' untuk memulai.")