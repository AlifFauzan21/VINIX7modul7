# ============================================
# 🚗 Auto MPG Dashboard (Improved Version)
# ============================================

import pandas as pd
import numpy as np
import panel as pn
import hvplot.pandas
from ucimlrepo import fetch_ucirepo

pn.extension('tabulator', 'floatpanel')

# -----------------------------
# 1️⃣ Load dataset dari ucimlrepo
# -----------------------------
auto_mpg = fetch_ucirepo(id=9)
X = auto_mpg.data.features
y = auto_mpg.data.targets
df = pd.concat([X, y], axis=1)

# Normalisasi nama kolom
df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

# Tambah kolom dummy kalau perlu
if 'car_name' not in df.columns:
    df['car_name'] = ['Mobil-' + str(i) for i in range(len(df))]

# Bersihkan data
df['horsepower'] = pd.to_numeric(df['horsepower'], errors='coerce')
df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
df['model_year'] = pd.to_numeric(df['model_year'], errors='coerce')
df.dropna(subset=['mpg', 'horsepower', 'weight', 'model_year'], inplace=True)

# Normalisasi kolom origin
if df['origin'].dtype == 'O':
    df['origin_name'] = df['origin'].str.title()
else:
    origin_map = {1: 'USA', 2: 'Europe', 3: 'Japan'}
    df['origin_name'] = df['origin'].map(origin_map)

# -----------------------------
# 2️⃣ Widgets (filter)
# -----------------------------
origin_select = pn.widgets.MultiSelect(
    name='Asal Mobil',
    options=sorted(df['origin_name'].dropna().unique().tolist()),
    value=sorted(df['origin_name'].dropna().unique().tolist())
)

cyl_select = pn.widgets.MultiSelect(
    name='Jumlah Silinder',
    options=sorted(df['cylinders'].unique().tolist()),
    value=sorted(df['cylinders'].unique().tolist())
)

year_slider = pn.widgets.IntRangeSlider(
    name='Tahun Model',
    start=int(df['model_year'].min()),
    end=int(df['model_year'].max()),
    value=(int(df['model_year'].min()), int(df['model_year'].max()))
)

# -----------------------------
# 3️⃣ Data filter function
# -----------------------------
@pn.depends(origin_select, cyl_select, year_slider)
def get_filtered_data(origin_select, cyl_select, year_slider):
    return df[
        (df['origin_name'].isin(origin_select)) &
        (df['cylinders'].isin(cyl_select)) &
        (df['model_year'].between(year_slider[0], year_slider[1]))
    ]

# -----------------------------
# 4️⃣ Metrics Cards
# -----------------------------
@pn.depends(origin_select, cyl_select, year_slider)
def summary_cards(origin_select, cyl_select, year_slider):
    dff = get_filtered_data(origin_select, cyl_select, year_slider)
    if dff.empty:
        return pn.Row(pn.pane.Markdown("**Tidak ada data untuk filter ini.**"))
    avg_mpg = round(dff['mpg'].mean(), 2)
    avg_weight = int(dff['weight'].mean())
    count = len(dff)
    return pn.Row(
        pn.indicators.Number(name='Rata-rata MPG', value=avg_mpg, format='{value}'),
        pn.indicators.Number(name='Berat Rata-rata', value=avg_weight, format='{value:,} lbs'),
        pn.indicators.Number(name='Jumlah Data', value=count, format='{value}')
    )

# -----------------------------
# 5️⃣ Plots + Insight
# -----------------------------
@pn.depends(origin_select, cyl_select, year_slider)
def plot_distribution(origin_select, cyl_select, year_slider):
    dff = get_filtered_data(origin_select, cyl_select, year_slider)
    if dff.empty:
        return pn.pane.Markdown("Tidak ada data untuk filter ini.")
    return dff.hvplot.hist('mpg', bins=20, color='seagreen', width=450, height=300, title='Distribusi Efisiensi Bahan Bakar (MPG)')

@pn.depends(origin_select, cyl_select, year_slider)
def plot_cylinders(origin_select, cyl_select, year_slider):
    dff = get_filtered_data(origin_select, cyl_select, year_slider)
    if dff.empty:
        return pn.pane.Markdown("Tidak ada data untuk filter ini.")
    avg = dff.groupby('cylinders')['mpg'].mean().reset_index()
    return avg.hvplot.bar(x='cylinders', y='mpg', color='darkorange', width=450, height=300, title='Rata-rata MPG Berdasarkan Silinder')

@pn.depends(origin_select, cyl_select, year_slider)
def plot_relation(origin_select, cyl_select, year_slider):
    dff = get_filtered_data(origin_select, cyl_select, year_slider)
    if dff.empty:
        return pn.pane.Markdown("Tidak ada data untuk filter ini.")
    return dff.hvplot.scatter('weight', 'mpg', by='origin_name', width=900, height=400, alpha=0.7, legend='top', title='Hubungan Berat Mobil dan Efisiensi (MPG)')

@pn.depends(origin_select, cyl_select, year_slider)
def text_insight(origin_select, cyl_select, year_slider):
    dff = get_filtered_data(origin_select, cyl_select, year_slider)
    if dff.empty:
        return pn.pane.Markdown(" ")
    insight = f"""
### 💡 Insight Otomatis:
- Rata-rata efisiensi bahan bakar: **{dff['mpg'].mean():.2f} MPG**
- Mobil dengan silinder lebih sedikit umumnya memiliki efisiensi bahan bakar yang lebih tinggi.
- Terdapat korelasi negatif antara berat mobil dan MPG — semakin berat, semakin boros.
"""
    return pn.pane.Markdown(insight)

# -----------------------------
# 6️⃣ Layout: Material Template
# -----------------------------
template = pn.template.MaterialTemplate(
    title="🚗 Dashboard Analisis Auto MPG",
    sidebar=[pn.pane.Markdown("### 🔧 Filter Data"), origin_select, cyl_select, year_slider],
)

template.main.append(
    pn.Column(
        pn.pane.Markdown("""
## ✨ Analisis Dataset Auto MPG
Dashboard ini menampilkan analisis interaktif dari dataset **Auto MPG**.
Tujuan dashboard ini untuk membantu pengguna awam memahami:
1. Distribusi efisiensi bahan bakar (MPG)
2. Perbandingan berdasarkan jumlah silinder
3. Hubungan antara berat mobil dan efisiensi bahan bakar
"""),
        summary_cards,
        pn.Row(plot_distribution, plot_cylinders),
        pn.Spacer(height=10),
        plot_relation,
        pn.Spacer(height=10),
        text_insight,
    )
)

# -----------------------------
# 7️⃣ Jalankan
# -----------------------------
template.servable()

