import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.io as pio

# Városok
varosok = ['Pécs', 'Budapest', 'Győr', 'Miskolc', 'Szeged']

# Adat generálás
np.random.seed(42)
adatok = []

# Segédfüggvény: hányadik adott hét napja a hónapban
def get_nth_weekday_in_month(d):
    return ((d.day - 1) // 7) + 1

# 2021-2024 adatok
for ev in range(2021, 2025):
    datumok = pd.date_range(f'{ev}-08-01', f'{ev}-08-31')
    for datum in datumok:
        for varos in varosok:
            latogato = np.random.randint(800, 1001)
            if datum.weekday() == 4:  # péntek
                latogato = int(latogato * 1.1)
            elif datum.weekday() == 5:  # szombat
                latogato = int(latogato * 1.35)
            elif datum.weekday() == 6:  # vasárnap
                latogato = int(latogato * 1.3)
            adatok.append({
                'varos': varos,
                'datum': datum,
                'latogatok_szama': latogato,
                'ev': ev,
                'het_napja': datum.weekday(),
                'nth_weekday': get_nth_weekday_in_month(datum)
            })

df = pd.DataFrame(adatok)

# 2025 dátumok
datumok_2025 = pd.date_range('2025-08-01', '2025-08-31')
pred_df = pd.DataFrame({
    'datum': datumok_2025
})
pred_df['het_napja'] = pred_df['datum'].dt.weekday
pred_df['nth_weekday'] = pred_df['datum'].apply(get_nth_weekday_in_month)

# Prediktált értékek
predikcio = []
for varos in varosok:
    for _, row in pred_df.iterrows():
        mask = (
            (df['varos'] == varos) &
            (df['het_napja'] == row['het_napja']) &
            (df['nth_weekday'] == row['nth_weekday'])
        )
        atlag = df.loc[mask, 'latogatok_szama'].mean()
        predikcio.append({
            'varos': varos,
            'datum': row['datum'],
            'pred_latogatok': int(atlag) if not np.isnan(atlag) else 0
        })

pred_df_final = pd.DataFrame(predikcio)
pred_df_final['honap'] = pred_df_final['datum'].dt.month

# Számítsd ki az arányokat
for varos in varosok:
    mask = pred_df_final['varos'] == varos
    ossz = pred_df_final.loc[mask, 'pred_latogatok'].sum()
    pred_df_final.loc[mask, 'havi_arany'] = pred_df_final.loc[mask, 'pred_latogatok'] / ossz * 100

# Múlt évek arányok
df['honap'] = df['datum'].dt.month
df['ev_havi_arany'] = 0.0
for varos in varosok:
    for ev in range(2021, 2025):
        mask = (df['varos'] == varos) & (df['ev'] == ev)
        ossz = df.loc[mask, 'latogatok_szama'].sum()
        df.loc[mask, 'ev_havi_arany'] = df.loc[mask, 'latogatok_szama'] / ossz * 100

# Riport generálása
html_parts = ""

for varos in varosok:
    fig1 = go.Figure()
    fig2 = go.Figure()

    # Előző évek
    for ev in range(2021, 2025):
        df_ev = df[(df['varos'] == varos) & (df['ev'] == ev)]
        # párosítsd 2025 dátumokhoz
        paired = []
        for _, row in pred_df.iterrows():
            match = df_ev[
                (df_ev['het_napja'] == row['het_napja']) &
                (df_ev['nth_weekday'] == row['nth_weekday'])
            ]
            if not match.empty:
                matched_datum = match.iloc[0]
                paired.append({
                    'datum_2025': row['datum'],
                    'latogatok': matched_datum['latogatok_szama'],
                    'arany': matched_datum['ev_havi_arany'],
                    'eredeti_datum': matched_datum['datum'].strftime('%Y-%m-%d')
                })
        paired_df = pd.DataFrame(paired)

        fig1.add_trace(go.Scatter(
            x=paired_df['datum_2025'],
            y=paired_df['latogatok'],
            mode='lines+markers',
            name=f'{ev} adat'
        ))
        fig2.add_trace(go.Scatter(
            x=paired_df['datum_2025'],
            y=paired_df['arany'],
            mode='lines+markers',
            name=f'{ev} adat'
        ))

    # 2025 predikció
    df_2025 = pred_df_final[pred_df_final['varos'] == varos]
    fig1.add_trace(go.Scatter(
        x=df_2025['datum'],
        y=df_2025['pred_latogatok'],
        mode='lines+markers',
        name='2025 predikció',
        line=dict(color='black', width=4, dash='dash')
    ))
    fig2.add_trace(go.Scatter(
        x=df_2025['datum'],
        y=df_2025['havi_arany'],
        mode='lines+markers',
        name='2025 predikció',
        line=dict(color='black', width=4, dash='dash')
    ))

    # Layout
    fig1.update_layout(
        title=f"{varos} - Látogatók száma 2025 augusztus (összepárosított napokkal)",
        xaxis_title="2025 augusztus napjai",
        yaxis_title="Látogatók száma"
    )
    fig2.update_layout(
        title=f"{varos} - Napi arány % 2025 augusztus (összepárosított napokkal)",
        xaxis_title="2025 augusztus napjai",
        yaxis_title="Havi arány %"
    )

    # Fejléc szöveg: nap párosítások
    paired_text = "<ul>"
    for ev in range(2021, 2025):
        paired_text += f"<li>{ev}: "
        df_ev = df[(df['varos'] == varos) & (df['ev'] == ev)]
        days = []
        for _, row in pred_df.iterrows():
            match = df_ev[
                (df_ev['het_napja'] == row['het_napja']) &
                (df_ev['nth_weekday'] == row['nth_weekday'])
            ]
            if not match.empty:
                matched_datum = match.iloc[0]
                days.append(f"{matched_datum['datum'].strftime('%Y-%m-%d')}")
        paired_text += ", ".join(days) + "</li>"
    paired_text += "</ul>"

    html_parts += f"<h2>{varos}</h2>"
    html_parts += paired_text
    html_parts += pio.to_html(fig1, include_plotlyjs=False, full_html=False)
    html_parts += pio.to_html(fig2, include_plotlyjs=False, full_html=False)

# Teljes HTML
html_full = """
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
""" + html_parts + """
</body>
</html>
"""

pred_df_final.to_csv('turista_predikcio_2025_augusztus_vonal.csv', index=False)

with open("turista_predikcio_2025_augusztus_vonal.html", "w") as f:
    f.write(html_full)

print("Riport generálva: turista_predikcio_2025_augusztus_vonal.html")
