# -*- coding: utf-8 -*-
"""
Hybrid Mass Shooting Report Generator (MJ + GVA)
Requirements:
  - pandas
  - plotly
  - requests
"""

import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# -------------------------------
# 1️⃣ Download CSVs or load local
# -------------------------------

# Mother Jones CSV (ArcGIS / GitHub mirror)
MJ_CSV_URL = "https://gist.githubusercontent.com/rlvaugh/beed70510dcff259aeb120f0abf63533/raw/mass_shootings.csv"

# Gun Violence Archive CSV (The Trace Data Hub)
GVA_CSV_URL = "https://datahub.io/JohnDoe/mass-shootings/r/mass-shootings.csv"  # Replace with actual URL

def download_csv(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        return StringIO(resp.text)
    else:
        raise ValueError(f"Failed to download CSV from {url}")

# Load datasets
mj_df = pd.read_csv(download_csv(MJ_CSV_URL))
gva_df = pd.read_csv(download_csv(GVA_CSV_URL))

# -------------------------------
# 2️⃣ Parse & normalize columns
# -------------------------------

# MJ dataset
# Columns: Date, State, City, Killed, Injured, School
mj_df['Date'] = pd.to_datetime(mj_df['Date'])
mj_df['Year'] = mj_df['Date'].dt.year
mj_df['School'] = mj_df.get('School', False)  # If missing, default False
mj_df['MJ_Count'] = 1  # Each row counts as 1 incident

# GVA dataset
# Columns: Incident Date, State, City, # Killed, # Injured, Total Victims, School
gva_df['Incident Date'] = pd.to_datetime(gva_df['Incident Date'])
gva_df['Year'] = gva_df['Incident Date'].dt.year
gva_df['School'] = gva_df.get('School', False)
gva_df['GVA_Count'] = 1

# -------------------------------
# 3️⃣ Aggregate by Year x State
# -------------------------------

mj_agg = mj_df.groupby(['Year', 'State']).agg(
    MJ_Count=('MJ_Count','sum'),
    School_Incidents=('School','sum')
).reset_index()

gva_agg = gva_df.groupby(['Year', 'State']).agg(
    GVA_Count=('GVA_Count','sum'),
    School_Incidents=('School','sum')
).reset_index()

# Merge MJ and GVA aggregates
combined = pd.merge(
    mj_agg, gva_agg, on=['Year','State'], how='outer', suffixes=('_MJ','_GVA')
).fillna(0)

# For HTML, mark ★ for school shootings
def school_marker(row):
    if row['School_Incidents_MJ'] > 0 or row['School_Incidents_GVA'] > 0:
        return '★'
    return ''

combined['School'] = combined.apply(school_marker, axis=1)

# -------------------------------
# 4️⃣ Generate HTML Table
# -------------------------------

html_table = combined.to_html(
    columns=['Year','State','MJ_Count','GVA_Count','School'],
    index=False,
    border=1,
    justify='center',
    classes='mass-shooting-table'
)

# -------------------------------
# 5️⃣ Generate Trend Chart (National totals)
# -------------------------------

national_trend = combined.groupby('Year').agg(
    MJ_Total=('MJ_Count','sum'),
    GVA_Total=('GVA_Count','sum')
).reset_index()

fig = px.line(
    national_trend,
    x='Year',
    y=['MJ_Total','GVA_Total'],
    labels={'value':'Mass Shootings','variable':'Dataset'},
    title='National Mass Shooting Trend (MJ vs GVA)'
)
trend_chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

# -------------------------------
# 6️⃣ Export full HTML report
# -------------------------------

html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Hybrid Mass Shooting Report (MJ + GVA)</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
h1 {{ color: #003366; }}
.mass-shooting-table th {{ background-color: #f2f2f2; padding: 5px; }}
.mass-shooting-table td {{ padding: 5px; text-align: center; }}
.school {{ color: red; font-weight: bold; }}
</style>
</head>
<body>
<h1>U.S. Mass Shootings — Hybrid MJ + GVA</h1>
<p>School shootings are marked with <span class="school">★</span>.</p>

<h2>State x Year Mass Shootings Table</h2>
{html_table}

<h2>National Trend Chart</h2>
{trend_chart_html}

<h2>U.S. Map Placeholder</h2>
<img src="https://via.placeholder.com/800x400?text=State+Mass+Shooting+Map+Placeholder" alt="State Mass Shooting Map">
<p>Replace with dynamic map once full data processed.</p>

</body>
</html>
"""

# Save HTML
with open('mass_shootings_report.html','w', encoding='utf-8') as f:
    f.write(html_content)

print("HTML report generated: mass_shootings_report.html")
