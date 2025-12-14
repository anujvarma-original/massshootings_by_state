# mass_shootings_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

st.set_page_config(page_title="US Mass Shootings Analysis", layout="wide")

st.title("U.S. Mass Shootings — Hybrid MJ + GVA")

st.markdown("""
This app allows you to upload **Mother Jones (MJ)** and **Gun Violence Archive (GVA)** CSVs, aggregates mass shootings by **Year × State**, marks **school shootings**, and displays tables and charts.
""")

# ----------------------------------------
# 1️⃣ Upload CSVs
# ----------------------------------------
mj_file = st.file_uploader("Upload Mother Jones CSV", type=["csv"])
gva_file = st.file_uploader("Upload GVA CSV", type=["csv"])

if mj_file and gva_file:
    # Load CSVs
    mj_df = pd.read_csv(mj_file)
    gva_df = pd.read_csv(gva_file)

    # ----------------------------------------
    # 2️⃣ Parse & normalize
    # ----------------------------------------
    # MJ
    mj_df['Date'] = pd.to_datetime(mj_df['Date'], errors='coerce')
    mj_df['Year'] = mj_df['Date'].dt.year
    mj_df['School'] = mj_df.get('School', False)
    mj_df['MJ_Count'] = 1

    # GVA
    gva_df['Incident Date'] = pd.to_datetime(gva_df['Incident Date'], errors='coerce')
    gva_df['Year'] = gva_df['Incident Date'].dt.year
    gva_df['School'] = gva_df.get('School', False)
    gva_df['GVA_Count'] = 1

    # ----------------------------------------
    # 3️⃣ Aggregate Year × State
    # ----------------------------------------
    mj_agg = mj_df.groupby(['Year','State']).agg(
        MJ_Count=('MJ_Count','sum'),
        School_Incidents=('School','sum')
    ).reset_index()

    gva_agg = gva_df.groupby(['Year','State']).agg(
        GVA_Count=('GVA_Count','sum'),
        School_Incidents=('School','sum')
    ).reset_index()

    combined = pd.merge(
        mj_agg, gva_agg, on=['Year','State'], how='outer', suffixes=('_MJ','_GVA')
    ).fillna(0)

    combined['School'] = combined.apply(lambda row: '★' if row['School_Incidents_MJ']>0 or row['School_Incidents_GVA']>0 else '', axis=1)

    # ----------------------------------------
    # 4️⃣ Display Table
    # ----------------------------------------
    st.subheader("State × Year Mass Shootings Table")
    st.dataframe(combined[['Year','State','MJ_Count','GVA_Count','School']])

    # ----------------------------------------
    # 5️⃣ National Trend Chart
    # ----------------------------------------
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
    st.subheader("National Mass Shooting Trend")
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------
    # 6️⃣ Optional: U.S. Map Placeholder
    # ----------------------------------------
    st.subheader("U.S. Map — Mass Shooting Density by State (Placeholder)")
    st.image("https://via.placeholder.com/800x400?text=State+Mass+Shooting+Map+Placeholder")
    st.markdown("Replace with dynamic choropleth once full state-level data is available.")

else:
    st.info("Upload both Mother Jones and GVA CSV files to proceed.")
