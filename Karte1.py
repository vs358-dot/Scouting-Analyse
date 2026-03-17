# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 11:17:30 2026

@author: veren
"""
import pandas as pd
import folium
import streamlit as st
from cleaning import clean_data

def create_transfer_map():
    """
    Erstellt eine interaktive FCA-Transferkarte (Folium + Streamlit)
    
    Funktionen der Karte:
    - Visualisierung von Spieler-Zugängen und Abgängen zum/vom FCA
    - Darstellung als Linien (Flows) auf einer Karte
    - Filter nach:
      • Im Verein seit
      • Geburtsjahr
      • Flow-Typ (Zugänge / Abgänge / Alle)
      • Zeitraum (abhängig vom Flow-Typ)
      • Region (abhängig vom Flow-Typ)
      • Status / Status2
      • Top-N Vereinen
    
    Farblogik:
    - Blau: Zugänge
    - Rot: Abgänge

    Rückgabewert:
    - Folium Map-Objekt zur Darstellung in Streamlit
    """
    # Konstanten & Spaltennamen 
    COL_FROM, COL_TO = "abgebender Verein", "aufnehmender Verein"
    COL_VEREIN = "verein"
    FCA_LAT, FCA_LON = 48.36, 10.90


    # Prüfen, ob Daten geladen wurden
    if "players_df" not in st.session_state \
       or "vereine_df" not in st.session_state \
       or "regionen_df" not in st.session_state:
        st.error("Bitte lade alle benötigten Dateien hoch!")
        return
    # Daten laden & bereinigen
    df = clean_data(st.session_state["players_df"])
    addr = st.session_state["vereine_df"]
    regions = st.session_state["regionen_df"]

    # Sidebar-Filter
    # -------------------------------------------
    # --- Sidebar Filter ---
    verein_list = ["Alle"] + sorted(df["Im Verein"].dropna().unique())
    selected_verein = st.sidebar.selectbox("Im Verein:", verein_list)

    stufen_order = ["U08","U09","U10","U11","U12","U13","U14","U15","U16","U17","U19","U21/U23"]
    selected_stufe = st.sidebar.selectbox("Im Verein seit:", ["Alle"] + stufen_order)

    flow_type = st.sidebar.selectbox("Flow-Typ:", ["Alle", "Zugänge", "Abgänge"], index=0)
    top_n = st.sidebar.selectbox("Top-N Vereine anzeigen", [10, 20, 30, 50, "Alle"], index=2)
    top_n_val = None if top_n == "Alle" else int(top_n)

    # --- 1. Vorfilter (OHNE Geburtsjahr!) ---
    df_pre = df.copy()

    if selected_stufe != "Alle":
        df_pre = df_pre[df_pre["im Verein seit"].astype(str).str.lower() == selected_stufe.lower()]

    if selected_verein != "Alle":
        df_pre = df_pre[df_pre["Im Verein"].str.lower() == selected_verein.lower()]

    # --- Slider-Grenzen aus vorgefilterten Daten ---
    if df_pre.empty:
        st.sidebar.warning("Keine Daten für diese Auswahl")
        st.stop()

    min_y = int(df_pre["Geburtsjahr"].min())
    max_y = int(df_pre["Geburtsjahr"].max())

    # --- Slider ABSICHERN ---
    if min_y == max_y:
        jahrgang = (min_y, max_y)
        st.sidebar.write(f"Geburtsjahr: {min_y}")
    else:
        jahrgang = st.sidebar.slider(
            "Geburtsjahr:",
            min_y,
            max_y,
            (min_y, max_y)
        )

    # --- 2. Finaler Filter (inkl. Jahrgang) ---
    df = df_pre[
        (df_pre["Geburtsjahr"] >= jahrgang[0]) &
        (df_pre["Geburtsjahr"] <= jahrgang[1])
    ]

    
    # -------------------------------------------
    
    
    # Zugänge/Abgänge: Jahrgangsfilter + Region
    # -------------------------------------------
    selected_region = None

    if flow_type == "Zugänge":
        years = sorted(df["Privatspielberechtigt seit"].dropna().dt.year.unique())
    
        if len(years) == 0:
            st.sidebar.warning("Keine Zugänge für diese Auswahl")
            st.stop()
    
        min_y, max_y = min(years), max(years)
    
        if min_y == max_y:
            yrange = (min_y, max_y)
            st.sidebar.write(f"Jahr der Privatspielberechtigung: {min_y}")
        else:
            yrange = st.sidebar.slider(
                "Jahr der Privatspielberechtigung:",
                min_y, max_y,
                (min_y, max_y)
            )
    
        df = df[df["Privatspielberechtigt seit"].dt.year.between(yrange[0], yrange[1])]


        # Regionenfilter (nur Herkunftsvereine)
        region_names = sorted(addr["region"].dropna().unique())
        selected_region = st.sidebar.selectbox(
            "Region auswählen:",
            options=["Alle"] + region_names + ["Außerhalb aller Regionen"]
        )
        status_list = ["Alle"] + sorted(df["Status"].dropna().unique())
        selected_status = st.sidebar.selectbox("Status:", status_list)
        
        if selected_status != "Alle":
            df = df[df["Status"].astype(str).str.lower() == selected_status.lower()]
        
    elif flow_type == "Abgänge":
        years = sorted(df["Abmeldedatum"].dropna().dt.year.unique())
    
        if len(years) == 0:
            st.sidebar.info("Keine Abgänge vorhanden")
            st.stop()
    
        min_y, max_y = min(years), max(years)
    
        if min_y == max_y:
            yrange = (min_y, max_y)
            st.sidebar.write(f"Jahr des Abmeldedatums: {min_y}")
        else:
            yrange = st.sidebar.slider(
                "Jahr des Abmeldedatums:",
                min_y, max_y,
                (min_y, max_y)
            )
    
        df = df[df["Abmeldedatum"].dt.year.between(*yrange)]

        region_names = sorted(addr["region"].dropna().unique())
        selected_region = st.sidebar.selectbox(
            "Region auswählen:",
            options=["Alle"] + region_names + ["Außerhalb aller Regionen"]
        )
        
        status_list = ["Alle"] + sorted(df["Status2"].dropna().unique())
        selected_status = st.sidebar.selectbox("Status2:", status_list)
        
        if selected_status != "Alle":
            df = df[df["Status2"].astype(str).str.lower() == selected_status.lower()]
    # -------------------------------------------
    
    
    # Vereins-Geodaten verbinden
    # -------------------------------------------
    addr = addr.rename(columns={COL_VEREIN: "verein"})

    def merge_geo(df_rows, col):
        """Holt Vereine + Geo + Region"""
        return df_rows.merge(
            addr[["verein", "lat", "lon", "region"]],
            how="left",
            left_on=col,
            right_on="verein"
        )
    # -------------------------------------------
    
    
    # Regionsfilter-Funktion
    # -------------------------------------------
    def apply_region_filter(df_geo, region_col):
        if selected_region is None or selected_region == "Alle":
            return df_geo
        if selected_region == "Außerhalb aller Regionen":
            return df_geo[df_geo[region_col].isna()]
        return df_geo[df_geo[region_col] == selected_region]
    # -------------------------------------------
    
    
    # Flow-Berechnung nach deinen Regeln
    # -------------------------------------------
    def get_flows(df_rows, col):
        """Erstellt Liste mit Verein + Count + Geo"""
        counts = (
            df_rows.dropna(subset=[col])[col]
            .astype(str)
            .value_counts()
            .reset_index()
        )
        counts.columns = ["verein", "count"]
        return counts.merge(addr, on="verein").dropna(subset=["lat", "lon"])


    # Logik für die drei Flow-Typen

    in_geo = pd.DataFrame()
    out_geo = pd.DataFrame()

    # ZUGÄNGE -----------------------------------
    if flow_type in ["Zugänge", "Alle"]:
        df_from = merge_geo(df, COL_FROM).rename(columns={"region": "region_from"})
        if flow_type == "Zugänge":
            df_from = apply_region_filter(df_from, "region_from")
        in_geo = get_flows(df_from, COL_FROM)
        if top_n_val:
            in_geo = in_geo.head(top_n_val)

    # ABGÄNGE -----------------------------------
    if flow_type in ["Abgänge", "Alle"]:
        df_to = merge_geo(df, COL_TO).rename(columns={"region": "region_to"})
        if flow_type == "Abgänge":
            df_to = apply_region_filter(df_to, "region_to")
        out_geo = get_flows(df_to, COL_TO)
        if top_n_val:
            out_geo = out_geo.head(top_n_val)


    # Linienbreite
    def line_width(count, max_val):
        return 1 + 17 * (count / max_val)
    # -------------------------------------------
    
    
    # Karte erzeugen
    # -------------------------------------------
    m = folium.Map(location=[FCA_LAT, FCA_LON], zoom_start=7)

    # Regionen einzeichnen
    if not regions.empty:
        name_col = "Name" if "Name" in regions.columns else regions.columns[0]
        folium.GeoJson(
            regions,
            style_function=lambda x: {"fillOpacity": 0.05, "weight": 1, "color": "black"},
            highlight_function=lambda x: {"weight": 3, "color": "red"},
            tooltip=folium.features.GeoJsonTooltip(fields=[name_col])
        ).add_to(m)
    
    
    # Zugänge (blau)
    # -------------------------------------------
    if not in_geo.empty:
        max_in = in_geo["count"].max()
        for _, row in in_geo.iterrows():
            folium.PolyLine(
                [(row["lat"], row["lon"]), (FCA_LAT, FCA_LON)],
                weight=line_width(row["count"], max_in),
                color="blue", opacity=0.6,
                tooltip=f"{row['verein']} → FCA ({row['count']})"
            ).add_to(m)
    # -------------------------------------------
    
    # Abgänge (rot)
    # -------------------------------------------
    if not out_geo.empty:
        max_out = out_geo["count"].max()
        for _, row in out_geo.iterrows():
            folium.PolyLine(
                [(FCA_LAT, FCA_LON), (row["lat"], row["lon"])],
                weight=line_width(row["count"], max_out),
                color="red", opacity=0.6,
                tooltip=f"FCA → {row['verein']} ({row['count']})"
            ).add_to(m)
    # -------------------------------------------
    
    # FCA-Marker
    # -------------------------------------------
    folium.CircleMarker(
        (FCA_LAT, FCA_LON),
        radius=7, color="black", fill=True, fill_color="yellow",
        tooltip="FC Augsburg"
    ).add_to(m)
    # -------------------------------------------
    
    
    # Vereinsmarker
    # Nur Vereine aus in_geo/out_geo (Top-N relevant!)
    # -------------------------------------------
    clubs = pd.concat([in_geo, out_geo]).drop_duplicates("verein")
    for _, row in clubs.iterrows():
        folium.CircleMarker(
            (row["lat"], row["lon"]),
            radius=3, color="black", fill=True, fill_color="white",
            tooltip=row["verein"]
        ).add_to(m)
    # -------------------------------------------

    return m

